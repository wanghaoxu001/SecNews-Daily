import asyncio
import logging
import re
from datetime import datetime, timezone
from html import unescape
from typing import Any

import feedparser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rss_source import RssSource
from app.models.news import News
from app.models.enums import ProcessStatus

logger = logging.getLogger(__name__)


TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def _clean_html_like_text(text: str | None) -> str:
    if not text:
        return ""
    cleaned = unescape(text)
    cleaned = TAG_RE.sub(" ", cleaned)
    cleaned = WHITESPACE_RE.sub(" ", cleaned).strip()
    return cleaned


def _extract_summary(entry: Any) -> str:
    summary = entry.get("summary", "") or entry.get("description", "")
    return _clean_html_like_text(summary)


def _extract_content(entry: Any) -> str:
    """Extract full-content fields from RSS/Atom entry."""
    values: list[str] = []

    content_items = entry.get("content", [])
    if isinstance(content_items, dict):
        content_items = [content_items]

    if isinstance(content_items, list):
        for item in content_items:
            if isinstance(item, dict):
                value = item.get("value")
            else:
                value = getattr(item, "value", None)
            if value:
                values.append(value)

    # Fallback for some feeds exposing content via namespaced keys
    fallback_value = entry.get("content:encoded", "") or entry.get("content_encoded", "")
    if fallback_value:
        values.append(fallback_value)

    cleaned_values = [_clean_html_like_text(v) for v in values if v]
    cleaned_values = [v for v in cleaned_values if v]
    return "\n\n".join(cleaned_values)


def _parse_feed(url: str) -> list[dict]:
    """Parse RSS feed (blocking, run in executor)."""
    feed = feedparser.parse(url)
    entries = []
    for entry in feed.entries:
        published = None
        published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if published_parsed:
            published = datetime(*published_parsed[:6], tzinfo=timezone.utc)
        entries.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "summary": _extract_summary(entry),
            "content": _extract_content(entry),
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
            summary=entry.get("summary") or None,
            content=entry.get("content") or None,
            author=entry.get("author") or None,
            published_at=entry.get("published_at"),
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
