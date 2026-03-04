import logging
import time
import traceback
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import News
from app.models.rss_source import RssSource
from app.models.enums import ProcessStatus
from app.services.rss_fetcher import fetch_single_source
from app.services.news_processor import process_single_news_gen
from app.services.similarity_checker import check_similarity_for_news
from app.services.importance_judge import judge_importance_for_news

logger = logging.getLogger(__name__)


def _event(
    step: str,
    status: str,
    message: str,
    detail: str | None = None,
    duration_ms: int | None = None,
) -> dict:
    evt = {"step": step, "status": status, "message": message}
    if detail:
        evt["detail"] = detail
    if duration_ms is not None:
        evt["duration_ms"] = duration_ms
    return evt


async def run_source_pipeline(db: AsyncSession, source: RssSource) -> AsyncGenerator[dict, None]:
    """Run the full pipeline for a single RSS source, yielding progress events."""

    pipeline_start = time.monotonic()

    # Step 1: Fetch
    yield _event("fetch", "running", f"正在抓取 RSS 源: {source.name}...")
    t0 = time.monotonic()
    try:
        new_count = await fetch_single_source(db, source)
        elapsed = int((time.monotonic() - t0) * 1000)
        yield _event("fetch", "success", f"抓取完成，新增 {new_count} 篇文章", duration_ms=elapsed)
    except Exception as e:
        elapsed = int((time.monotonic() - t0) * 1000)
        yield _event("fetch", "error", f"RSS 抓取失败: {e}", traceback.format_exc(), duration_ms=elapsed)
        yield _event("done", "error", "流水线因抓取失败而终止")
        return

    if new_count == 0:
        yield _event("done", "success", "没有新文章，流水线结束")
        return

    # Step 2: Query new pending articles
    result = await db.execute(
        select(News).where(
            News.source_id == source.id,
            News.process_status == ProcessStatus.pending.value,
        )
    )
    pending_news = result.scalars().all()
    total = len(pending_news)
    yield _event("process", "info", f"共 {total} 篇待处理文章")

    processed_ok = 0
    processed_fail = 0

    for idx, news in enumerate(pending_news, 1):
        prefix = f"[{idx}/{total}] 《{news.title[:40]}》"

        # Step 3a: Process (translate/summarize/classify)
        yield _event("process", "running", f"{prefix} 开始处理...")
        t0 = time.monotonic()
        try:
            async for progress in process_single_news_gen(db, news):
                yield _event(
                    "process", "info",
                    f"{prefix} {progress['message']}",
                    detail=progress.get("detail"),
                    duration_ms=progress.get("duration_ms"),
                )

            if news.process_status == ProcessStatus.failed.value:
                processed_fail += 1
                elapsed = int((time.monotonic() - t0) * 1000)
                yield _event("process", "error", f"{prefix} 处理失败", news.process_error, duration_ms=elapsed)
                continue
        except Exception as e:
            processed_fail += 1
            elapsed = int((time.monotonic() - t0) * 1000)
            yield _event("process", "error", f"{prefix} 处理异常: {e}", traceback.format_exc(), duration_ms=elapsed)
            continue

        elapsed = int((time.monotonic() - t0) * 1000)
        yield _event("process", "success", f"{prefix} 基础处理完成", duration_ms=elapsed)

        # Step 3b: Similarity check
        yield _event("similarity", "running", f"{prefix} 正在检查相似性...")
        t0 = time.monotonic()
        try:
            await check_similarity_for_news(db, news)
            news.process_status = ProcessStatus.similarity_checked.value
            await db.commit()
            elapsed = int((time.monotonic() - t0) * 1000)
            sim_msg = f"与 ID={news.similar_to_id} 相似" if news.is_similar else "无相似文章"
            yield _event("similarity", "success", f"{prefix} 相似性检查完成: {sim_msg}", duration_ms=elapsed)
        except Exception as e:
            elapsed = int((time.monotonic() - t0) * 1000)
            yield _event("similarity", "error", f"{prefix} 相似性检查失败: {e}", traceback.format_exc(), duration_ms=elapsed)

        # Step 3c: Importance judgment
        yield _event("importance", "running", f"{prefix} 正在判断重要性...")
        t0 = time.monotonic()
        try:
            await judge_importance_for_news(db, news)
            news.process_status = ProcessStatus.completed.value
            await db.commit()
            elapsed = int((time.monotonic() - t0) * 1000)
            imp_msg = f"重要 - {news.importance_reason}" if news.is_important else "不重要"
            yield _event("importance", "success", f"{prefix} 重要性判断完成: {imp_msg}", duration_ms=elapsed)
        except Exception as e:
            elapsed = int((time.monotonic() - t0) * 1000)
            yield _event("importance", "error", f"{prefix} 重要性判断失败: {e}", traceback.format_exc(), duration_ms=elapsed)

        processed_ok += 1

    total_elapsed = int((time.monotonic() - pipeline_start) * 1000)
    yield _event("done", "success",
                 f"流水线完成: 共 {total} 篇，成功 {processed_ok} 篇，失败 {processed_fail} 篇",
                 duration_ms=total_elapsed)
