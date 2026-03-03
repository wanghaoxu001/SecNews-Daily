import logging
import re
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import News
from app.models.enums import ProcessStatus
from app.services.translator import translate_text, is_chinese
from app.services.content_crawler import crawl_article_content
from app.services.summarizer import generate_summary
from app.services.classifier import classify_news

logger = logging.getLogger(__name__)

MIN_RSS_CONTENT_LEN = 200
MIN_SUMMARY_ZH_LEN = 100
WHITESPACE_RE = re.compile(r"\s+")


def _progress(message: str, *, duration_ms: int | None = None, result: str | None = None) -> dict:
    p = {"message": message}
    if duration_ms is not None:
        p["duration_ms"] = duration_ms
    if result is not None:
        p["result"] = result
    return p


def _truncate(text: str, max_len: int = 80) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _content_length(text: str | None) -> int:
    if not text:
        return 0
    normalized = WHITESPACE_RE.sub(" ", text).strip()
    return len(normalized)


def _has_usable_content(text: str | None, min_len: int = MIN_RSS_CONTENT_LEN) -> bool:
    return _content_length(text) >= min_len


def _has_usable_summary(text: str | None, min_len: int = MIN_SUMMARY_ZH_LEN) -> bool:
    return _content_length(text) >= min_len


async def process_single_news_gen(db: AsyncSession, news: News):
    """Process a single pending news item as async generator, yielding progress dicts."""
    try:
        news.process_status = ProcessStatus.processing.value

        # Step 1: Get Chinese summary
        if _has_usable_summary(news.summary_zh):
            yield _progress("已有足够长度中文摘要，跳过")
        else:
            if not news.summary_zh and news.summary:
                # First pass: translate RSS summary when available.
                if is_chinese(news.summary):
                    news.summary_zh = news.summary
                    yield _progress("摘要已为中文，跳过翻译")
                else:
                    yield _progress("正在翻译摘要...")
                    t0 = time.monotonic()
                    news.summary_zh = await translate_text(db, news.summary)
                    elapsed = int((time.monotonic() - t0) * 1000)
                    yield _progress("摘要翻译完成", duration_ms=elapsed, result=_truncate(news.summary_zh))

            if _has_usable_summary(news.summary_zh):
                yield _progress("摘要长度达标，跳过补全")
            elif _has_usable_content(news.content):
                yield _progress("检测到 RSS 正文，正在生成中文摘要...")
                t0 = time.monotonic()
                news.summary_zh = await generate_summary(db, news.content or "")
                elapsed = int((time.monotonic() - t0) * 1000)
                yield _progress("摘要生成完成", duration_ms=elapsed, result=_truncate(news.summary_zh))
            else:
                if news.content:
                    yield _progress("RSS 正文过短，正在抓取文章正文...")
                elif news.summary_zh:
                    yield _progress("摘要偏短，正在抓取文章正文补全...")
                else:
                    yield _progress("正在抓取文章正文...")

                t0 = time.monotonic()
                crawled_content = await crawl_article_content(news.url)
                elapsed = int((time.monotonic() - t0) * 1000)
                if crawled_content:
                    news.content = crawled_content

                if _has_usable_content(news.content):
                    yield _progress("正文抓取完成", duration_ms=elapsed)
                    yield _progress("正在生成中文摘要...")
                    t0 = time.monotonic()
                    news.summary_zh = await generate_summary(db, news.content or "")
                    elapsed = int((time.monotonic() - t0) * 1000)
                    yield _progress("摘要生成完成", duration_ms=elapsed, result=_truncate(news.summary_zh))
                else:
                    if news.content:
                        yield _progress("正文抓取完成（内容较短）", duration_ms=elapsed)
                    else:
                        yield _progress("正文抓取完成（无内容）", duration_ms=elapsed)

                    # If crawling fails, keeping a short translated summary is acceptable.
                    if news.summary_zh:
                        logger.info(f"Crawl unavailable for news {news.id}; keeping short summary")
                        yield _progress("原文抓取失败，保留当前较短摘要")
                    else:
                        news.summary_zh = ""
                        logger.warning(f"No usable content or summary available for news {news.id}")
                        yield _progress("无法获取有效正文和摘要，摘要置空")

        # Step 2: Translate title
        if not news.title_zh:
            if is_chinese(news.title):
                news.title_zh = news.title
                yield _progress("标题已为中文，跳过翻译")
            else:
                yield _progress("正在翻译标题...")
                t0 = time.monotonic()
                news.title_zh = await translate_text(db, news.title)
                elapsed = int((time.monotonic() - t0) * 1000)
                yield _progress("标题翻译完成", duration_ms=elapsed, result=news.title_zh)
        else:
            yield _progress("已有中文标题，跳过")

        # Step 3: Classify
        if not news.category:
            yield _progress("正在分类...")
            t0 = time.monotonic()
            title_for_classify = news.title_zh or news.title
            summary_for_classify = news.summary_zh or news.summary or ""
            news.category = await classify_news(db, title_for_classify, summary_for_classify)
            elapsed = int((time.monotonic() - t0) * 1000)
            yield _progress(f"分类完成: {news.category}", duration_ms=elapsed)
        else:
            yield _progress(f"已有分类: {news.category}，跳过")

        news.process_status = ProcessStatus.processed.value
        news.process_error = None
        await db.commit()

    except Exception as e:
        logger.error(f"Failed to process news {news.id}: {e}")
        news.process_status = ProcessStatus.failed.value
        news.process_error = str(e)
        await db.commit()
        yield _progress(f"处理失败: {e}")


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
