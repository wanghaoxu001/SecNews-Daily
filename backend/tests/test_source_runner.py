from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import ProcessStatus
from app.services.source_runner import run_source_pipeline


def _make_pending_result(news_items: list[SimpleNamespace]) -> MagicMock:
    scalar_result = MagicMock()
    scalar_result.all.return_value = news_items
    result = MagicMock()
    result.scalars.return_value = scalar_result
    return result


@pytest.mark.asyncio
async def test_run_source_pipeline_passes_progress_detail():
    source = SimpleNamespace(id=1, name="Security Feed")
    news = SimpleNamespace(
        title="Example Incident",
        process_status=ProcessStatus.pending.value,
        similar_to_id=None,
        is_similar=False,
        is_important=False,
        importance_reason=None,
    )
    db = AsyncMock()
    db.execute.return_value = _make_pending_result([news])
    db.commit = AsyncMock()

    async def fake_process_gen(_db, item):
        item.process_status = ProcessStatus.processed.value
        yield {
            "message": "原文抓取失败，保留当前较短摘要",
            "detail": "crawl_error[BROWSER_MISSING] Playwright browser executable is missing",
        }

    with patch("app.services.source_runner.fetch_single_source", new=AsyncMock(return_value=1)), \
         patch("app.services.source_runner.process_single_news_gen", side_effect=fake_process_gen), \
         patch("app.services.source_runner.check_similarity_for_news", new=AsyncMock(return_value=None)), \
         patch("app.services.source_runner.judge_importance_for_news", new=AsyncMock(return_value=None)):
        events = [evt async for evt in run_source_pipeline(db, source)]

    assert any(
        evt["step"] == "process" and "crawl_error[BROWSER_MISSING]" in (evt.get("detail") or "")
        for evt in events
    )
