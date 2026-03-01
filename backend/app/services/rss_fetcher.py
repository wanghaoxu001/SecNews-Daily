import asyncio
import logging
from datetime import datetime, timezone

import feedparser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rss_source import RssSource
from app.models.news import News
from app.models.enums import ProcessStatus

logger = logging.getLogger(__name__)


def _parse_feed(url: str) -> list[dict]:
    """Parse RSS feed (blocking, run in executor)."""
    feed = feedparser.parse(url)
    entries = []
    for entry in feed.entries:
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        entries.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "author": entry.get("author", ""),
            "published_at": published,
        })
    return entries


async def fetch_single_source(db: AsyncSession, source: RssSource) -> int:
    """Fetch and deduplicate entries from a single RSS source. Returns count of new entries."""
    loop = asyncio.get_event_loop()
    try:
        entries = await loop.run_in_executor(None, _parse_feed, source.url)
    except Exception as e:
        logger.error(f"Failed to fetch RSS source {source.name}: {e}")
        return 0

    new_count = 0
    for entry in entries:
        if not entry["url"]:
            continue
        # Check URL uniqueness
        existing = await db.execute(select(News.id).where(News.url == entry["url"]))
        if existing.scalar_one_or_none() is not None:
            continue

        news = News(
            title=entry["title"],
            url=entry["url"],
            summary=entry["summary"] or None,
            author=entry["author"] or None,
            published_at=entry["published_at"],
            source_id=source.id,
            source_name=source.name,
            process_status=ProcessStatus.pending.value,
        )
        db.add(news)
        new_count += 1

    if new_count > 0:
        await db.commit()
    return new_count


async def fetch_all_sources(db: AsyncSession) -> dict:
    """Fetch all enabled RSS sources. Returns summary stats."""
    result = await db.execute(select(RssSource).where(RssSource.enabled == True))
    sources = result.scalars().all()

    total_new = 0
    errors = []
    for source in sources:
        try:
            count = await fetch_single_source(db, source)
            total_new += count
            logger.info(f"Fetched {count} new entries from {source.name}")
        except Exception as e:
            logger.error(f"Error fetching {source.name}: {e}")
            errors.append({"source": source.name, "error": str(e)})

    return {"total_new": total_new, "sources_processed": len(sources), "errors": errors}
