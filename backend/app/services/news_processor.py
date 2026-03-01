import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import News
from app.models.enums import ProcessStatus
from app.services.translator import translate_text, is_chinese
from app.services.content_crawler import crawl_article_content
from app.services.summarizer import generate_summary
from app.services.classifier import classify_news

logger = logging.getLogger(__name__)


async def process_single_news(db: AsyncSession, news: News) -> None:
    """Process a single pending news item: translate, summarize, classify."""
    try:
        news.process_status = ProcessStatus.processing.value

        # Step 1: Get Chinese summary
        if not news.summary_zh:
            if news.summary:
                # Path A: has summary → translate it
                if is_chinese(news.summary):
                    news.summary_zh = news.summary
                else:
                    news.summary_zh = await translate_text(db, news.summary)
            else:
                # Path B: no summary → crawl content and generate
                if not news.content:
                    news.content = await crawl_article_content(news.url)
                if news.content:
                    news.summary_zh = await generate_summary(db, news.content)
                else:
                    news.summary_zh = ""
                    logger.warning(f"No content available for news {news.id}")

        # Step 2: Translate title
        if not news.title_zh:
            if is_chinese(news.title):
                news.title_zh = news.title
            else:
                news.title_zh = await translate_text(db, news.title)

        # Step 3: Classify
        if not news.category:
            title_for_classify = news.title_zh or news.title
            summary_for_classify = news.summary_zh or news.summary or ""
            news.category = await classify_news(db, title_for_classify, summary_for_classify)

        news.process_status = ProcessStatus.processed.value
        news.process_error = None
        await db.commit()

    except Exception as e:
        logger.error(f"Failed to process news {news.id}: {e}")
        news.process_status = ProcessStatus.failed.value
        news.process_error = str(e)
        await db.commit()


async def process_pending_news(db: AsyncSession) -> dict:
    """Process all pending news items."""
    result = await db.execute(
        select(News).where(News.process_status == ProcessStatus.pending.value)
    )
    pending = result.scalars().all()

    processed = 0
    failed = 0
    for news in pending:
        try:
            await process_single_news(db, news)
            if news.process_status == ProcessStatus.processed.value:
                processed += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    return {"total": len(pending), "processed": processed, "failed": failed}
