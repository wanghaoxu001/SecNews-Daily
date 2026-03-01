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


async def process_single_news_gen(db: AsyncSession, news: News):
    """Process a single pending news item as async generator, yielding progress messages."""
    try:
        news.process_status = ProcessStatus.processing.value

        # Step 1: Get Chinese summary
        if not news.summary_zh:
            if news.summary:
                # Path A: has summary → translate it
                if is_chinese(news.summary):
                    news.summary_zh = news.summary
                    yield "摘要已为中文，跳过翻译"
                else:
                    yield "正在翻译摘要..."
                    news.summary_zh = await translate_text(db, news.summary)
                    yield "摘要翻译完成"
            else:
                # Path B: no summary → crawl content and generate
                if not news.content:
                    yield "正在抓取文章正文..."
                    news.content = await crawl_article_content(news.url)
                if news.content:
                    yield "正在生成中文摘要..."
                    news.summary_zh = await generate_summary(db, news.content)
                    yield "摘要生成完成"
                else:
                    news.summary_zh = ""
                    logger.warning(f"No content available for news {news.id}")
                    yield "无法获取正文内容，摘要置空"
        else:
            yield "已有中文摘要，跳过"

        # Step 2: Translate title
        if not news.title_zh:
            if is_chinese(news.title):
                news.title_zh = news.title
                yield "标题已为中文，跳过翻译"
            else:
                yield "正在翻译标题..."
                news.title_zh = await translate_text(db, news.title)
                yield "标题翻译完成"
        else:
            yield "已有中文标题，跳过"

        # Step 3: Classify
        if not news.category:
            yield "正在分类..."
            title_for_classify = news.title_zh or news.title
            summary_for_classify = news.summary_zh or news.summary or ""
            news.category = await classify_news(db, title_for_classify, summary_for_classify)
            yield f"分类完成: {news.category}"
        else:
            yield f"已有分类: {news.category}，跳过"

        news.process_status = ProcessStatus.processed.value
        news.process_error = None
        await db.commit()

    except Exception as e:
        logger.error(f"Failed to process news {news.id}: {e}")
        news.process_status = ProcessStatus.failed.value
        news.process_error = str(e)
        await db.commit()
        yield f"处理失败: {e}"


async def process_single_news(db: AsyncSession, news: News) -> None:
    """Process a single pending news item: translate, summarize, classify."""
    async for _ in process_single_news_gen(db, news):
        pass


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
