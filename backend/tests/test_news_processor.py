import pytest
from unittest.mock import patch, AsyncMock

from app.models.news import News
from app.models.enums import ProcessStatus
from app.services.news_processor import process_single_news, process_pending_news, process_single_news_gen
from app.services.content_crawler import CrawlError, CrawlResult

LONG_CONTENT = "This is a detailed incident report with technical indicators. " * 8
LONG_ZH_SUMMARY = "这是一段用于测试的较长中文摘要，覆盖事件背景、攻击路径、影响范围和处置建议，能够满足最小摘要长度要求。" * 2


def _crawl_result(
    content: str | None = None,
    error: CrawlError | None = None,
    attempts: int = 1,
    total_duration_ms: int = 1200,
) -> CrawlResult:
    return CrawlResult(
        content=content,
        error=error,
        attempts=attempts,
        total_duration_ms=total_duration_ms,
        attempt_errors=[error] if error else [],
    )


@pytest.mark.asyncio
async def test_process_news_path_a_with_summary(db_session):
    """Path A: news has English summary → translate summary and title, classify."""
    news = News(
        title="Critical RCE in Apache",
        url="https://example.com/rce-apache",
        summary="A critical remote code execution vulnerability was found in Apache HTTP Server.",
        process_status=ProcessStatus.pending.value,
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    with patch("app.services.news_processor.crawl_article_content_with_meta", new_callable=AsyncMock, return_value=_crawl_result()) as mock_crawl, \
         patch("app.services.news_processor.translate_text", new_callable=AsyncMock, return_value=LONG_ZH_SUMMARY), \
         patch("app.services.news_processor.classify_news", new_callable=AsyncMock, return_value="重大漏洞风险提示"):
        await process_single_news(db_session, news)

    assert news.process_status == ProcessStatus.processed.value
    assert news.summary_zh == LONG_ZH_SUMMARY
    assert news.title_zh is not None
    assert news.category == "重大漏洞风险提示"
    mock_crawl.assert_not_called()


@pytest.mark.asyncio
async def test_process_news_path_b_no_summary(db_session):
    """Path B: no summary → crawl content → generate summary."""
    news = News(
        title="Data Breach at Company X",
        url="https://example.com/breach-x",
        summary=None,
        process_status=ProcessStatus.pending.value,
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    with patch("app.services.news_processor.crawl_article_content_with_meta", new_callable=AsyncMock, return_value=_crawl_result(content=LONG_CONTENT)), \
         patch("app.services.news_processor.generate_summary", new_callable=AsyncMock, return_value="X公司发生重大数据泄露事件"), \
         patch("app.services.news_processor.translate_text", new_callable=AsyncMock, return_value="X公司数据泄露"), \
         patch("app.services.news_processor.classify_news", new_callable=AsyncMock, return_value="重大数据泄露事件"):
        await process_single_news(db_session, news)

    assert news.process_status == ProcessStatus.processed.value
    assert news.summary_zh == "X公司发生重大数据泄露事件"
    assert news.category == "重大数据泄露事件"


@pytest.mark.asyncio
async def test_process_news_prefers_rss_content_without_crawl(db_session):
    news = News(
        title="Supply Chain Compromise",
        url="https://example.com/supply-chain",
        summary="Short summary from RSS",
        content=LONG_CONTENT,
        process_status=ProcessStatus.pending.value,
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    with patch("app.services.news_processor.crawl_article_content_with_meta", new_callable=AsyncMock, return_value=_crawl_result()) as mock_crawl, \
         patch("app.services.news_processor.generate_summary", new_callable=AsyncMock, return_value="基于正文生成的摘要"), \
         patch("app.services.news_processor.translate_text", new_callable=AsyncMock, return_value="不会被调用"), \
         patch("app.services.news_processor.classify_news", new_callable=AsyncMock, return_value="供应链攻击与投毒事件"):
        await process_single_news(db_session, news)

    assert news.process_status == ProcessStatus.processed.value
    assert news.summary_zh == "基于正文生成的摘要"
    mock_crawl.assert_not_called()


@pytest.mark.asyncio
async def test_process_news_short_summary_triggers_crawl_and_regenerate(db_session):
    news = News(
        title="Weekly Update",
        url="https://example.com/weekly-update",
        summary="Vendor released a security update for multiple CVEs.",
        content="too short",
        process_status=ProcessStatus.pending.value,
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    with patch(
        "app.services.news_processor.crawl_article_content_with_meta",
        new_callable=AsyncMock,
        return_value=_crawl_result(content=LONG_CONTENT, attempts=2, total_duration_ms=3800),
    ) as mock_crawl, \
         patch("app.services.news_processor.generate_summary", new_callable=AsyncMock, return_value="抓取正文后生成更完整摘要"), \
         patch("app.services.news_processor.translate_text", new_callable=AsyncMock, return_value="厂商发布多个 CVE 的安全更新"), \
         patch("app.services.news_processor.classify_news", new_callable=AsyncMock, return_value="漏洞通告与补丁发布"):
        await process_single_news(db_session, news)

    assert news.process_status == ProcessStatus.processed.value
    assert news.summary_zh == "抓取正文后生成更完整摘要"
    assert news.crawl_attempts == 2
    assert news.crawl_last_duration_ms == 3800
    assert news.crawl_error_code is None
    assert news.crawl_error_detail is None
    mock_crawl.assert_called_once_with("https://example.com/weekly-update")


@pytest.mark.asyncio
async def test_process_news_short_summary_kept_when_crawl_fails(db_session):
    news = News(
        title="Weekly Update",
        url="https://example.com/weekly-update",
        summary="Vendor released a security update for multiple CVEs.",
        content="too short",
        process_status=ProcessStatus.pending.value,
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    with patch(
        "app.services.news_processor.crawl_article_content_with_meta",
        new_callable=AsyncMock,
        return_value=_crawl_result(
            content=None,
            error=CrawlError(
                code="NAV_TIMEOUT",
                message="Navigation timed out during crawling",
                url="https://example.com/weekly-update",
                retryable=True,
            ),
            attempts=3,
            total_duration_ms=9200,
        ),
    ) as mock_crawl, \
         patch("app.services.news_processor.translate_text", new_callable=AsyncMock, return_value="厂商发布多个 CVE 的安全更新"), \
         patch("app.services.news_processor.classify_news", new_callable=AsyncMock, return_value="漏洞通告与补丁发布"):
        await process_single_news(db_session, news)

    assert news.process_status == ProcessStatus.processed.value
    assert news.summary_zh == "厂商发布多个 CVE 的安全更新"
    assert news.crawl_error_code == "NAV_TIMEOUT"
    assert news.crawl_error_detail is not None and "attempts=3" in news.crawl_error_detail
    assert news.crawl_attempts == 3
    assert news.crawl_last_duration_ms == 9200
    assert news.crawl_last_attempt_at is not None
    mock_crawl.assert_called_once_with("https://example.com/weekly-update")


@pytest.mark.asyncio
async def test_process_news_emits_crawl_error_detail(db_session):
    news = News(
        title="Weekly Update",
        url="https://example.com/weekly-update",
        summary="Vendor released a security update for multiple CVEs.",
        content="too short",
        process_status=ProcessStatus.pending.value,
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    crawl_error = CrawlError(
        code="BROWSER_MISSING",
        message="Playwright browser executable is missing",
        url="https://example.com/weekly-update",
        retryable=False,
    )

    with patch(
        "app.services.news_processor.crawl_article_content_with_meta",
        new_callable=AsyncMock,
        return_value=_crawl_result(content=None, error=crawl_error, attempts=2, total_duration_ms=5100),
    ), patch(
        "app.services.news_processor.translate_text",
        new_callable=AsyncMock,
        return_value="厂商发布多个 CVE 的安全更新",
    ), patch(
        "app.services.news_processor.classify_news",
        new_callable=AsyncMock,
        return_value="漏洞通告与补丁发布",
    ):
        progress_events = [evt async for evt in process_single_news_gen(db_session, news)]

    assert any(
        "crawl_error[BROWSER_MISSING]" in (evt.get("detail") or "")
        and "attempts=2" in (evt.get("detail") or "")
        for evt in progress_events
    )


@pytest.mark.asyncio
async def test_process_news_short_rss_content_without_summary_triggers_crawl(db_session):
    news = News(
        title="Incident Timeline",
        url="https://example.com/incident-timeline",
        summary=None,
        content="short",
        process_status=ProcessStatus.pending.value,
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    with patch(
        "app.services.news_processor.crawl_article_content_with_meta",
        new_callable=AsyncMock,
        return_value=_crawl_result(content=LONG_CONTENT, attempts=1, total_duration_ms=1800),
    ) as mock_crawl, \
         patch("app.services.news_processor.generate_summary", new_callable=AsyncMock, return_value="抓取正文后生成摘要"), \
         patch("app.services.news_processor.translate_text", new_callable=AsyncMock, return_value="不会被调用"), \
         patch("app.services.news_processor.classify_news", new_callable=AsyncMock, return_value="网络攻击与入侵事件"):
        await process_single_news(db_session, news)

    assert news.process_status == ProcessStatus.processed.value
    assert news.summary_zh == "抓取正文后生成摘要"
    mock_crawl.assert_called_once_with("https://example.com/incident-timeline")


@pytest.mark.asyncio
async def test_process_news_idempotent(db_session):
    """Already-filled fields should not be re-processed."""
    news = News(
        title="Already Processed",
        url="https://example.com/already-processed",
        summary="Some summary",
        title_zh="已处理标题",
        summary_zh=LONG_ZH_SUMMARY,
        category="其他",
        process_status=ProcessStatus.pending.value,
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    # Should not call any LLM since all fields are filled
    with patch("app.services.news_processor.translate_text", new_callable=AsyncMock) as mock_translate, \
         patch("app.services.news_processor.classify_news", new_callable=AsyncMock) as mock_classify:
        await process_single_news(db_session, news)

    assert news.process_status == ProcessStatus.processed.value
    mock_translate.assert_not_called()
    mock_classify.assert_not_called()


@pytest.mark.asyncio
async def test_process_news_failure_marks_failed(db_session):
    """If processing fails, mark status as failed with error."""
    news = News(
        title="Will Fail",
        url="https://example.com/will-fail",
        summary="Some summary",
        process_status=ProcessStatus.pending.value,
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    with patch("app.services.news_processor.translate_text", new_callable=AsyncMock, side_effect=Exception("LLM down")):
        await process_single_news(db_session, news)

    assert news.process_status == ProcessStatus.failed.value
    assert "LLM down" in news.process_error


@pytest.mark.asyncio
async def test_process_pending_news_batch(db_session):
    """Batch processing of multiple pending news."""
    for i in range(3):
        news = News(
            title=f"Batch News {i}",
            url=f"https://example.com/batch-{i}",
            summary="Summary",
            process_status=ProcessStatus.pending.value,
        )
        db_session.add(news)
    await db_session.commit()

    with patch("app.services.news_processor.translate_text", new_callable=AsyncMock, return_value="翻译结果"), \
         patch("app.services.news_processor.classify_news", new_callable=AsyncMock, return_value="其他"):
        result = await process_pending_news(db_session)

    assert result["processed"] >= 3
