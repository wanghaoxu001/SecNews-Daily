import pytest
from unittest.mock import patch, AsyncMock

from app.models.news import News
from app.models.enums import ProcessStatus
from app.services.news_processor import process_single_news, process_pending_news


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

    with patch("app.services.news_processor.translate_text", new_callable=AsyncMock, return_value="Apache HTTP Server 发现严重远程代码执行漏洞"), \
         patch("app.services.news_processor.classify_news", new_callable=AsyncMock, return_value="重大漏洞风险提示"):
        await process_single_news(db_session, news)

    assert news.process_status == ProcessStatus.processed.value
    assert news.summary_zh is not None
    assert news.title_zh is not None
    assert news.category == "重大漏洞风险提示"


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

    with patch("app.services.news_processor.crawl_article_content", new_callable=AsyncMock, return_value="Full article text about the data breach..."), \
         patch("app.services.news_processor.generate_summary", new_callable=AsyncMock, return_value="X公司发生重大数据泄露事件"), \
         patch("app.services.news_processor.translate_text", new_callable=AsyncMock, return_value="X公司数据泄露"), \
         patch("app.services.news_processor.classify_news", new_callable=AsyncMock, return_value="重大数据泄露事件"):
        await process_single_news(db_session, news)

    assert news.process_status == ProcessStatus.processed.value
    assert news.summary_zh == "X公司发生重大数据泄露事件"
    assert news.category == "重大数据泄露事件"


@pytest.mark.asyncio
async def test_process_news_idempotent(db_session):
    """Already-filled fields should not be re-processed."""
    news = News(
        title="Already Processed",
        url="https://example.com/already-processed",
        summary="Some summary",
        title_zh="已处理标题",
        summary_zh="已有的中文摘要",
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
