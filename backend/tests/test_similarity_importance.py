import pytest
from unittest.mock import patch, AsyncMock

from app.models.news import News
from app.models.enums import ProcessStatus
from app.services.entity_extractor import extract_entities, entity_overlap_score
from app.services.keyword_analyzer import tfidf_cosine_similarity
from app.services.similarity_checker import check_similarity_for_news, _parse_similarity_json
from app.services.importance_judge import judge_importance_for_news, _parse_importance_json
from app.services.classifier import classify_news, _parse_classification_json


def test_extract_entities():
    text = "CVE-2024-1234 affects Microsoft Windows and Apache HTTP Server"
    entities = extract_entities(text)
    assert "cve-2024-1234" in entities
    assert "microsoft" in entities
    assert "apache" in entities


def test_entity_overlap():
    a = {"cve-2024-1234", "microsoft"}
    b = {"cve-2024-1234", "apache"}
    score = entity_overlap_score(a, b)
    assert 0 < score < 1


def test_entity_overlap_empty():
    assert entity_overlap_score(set(), {"a"}) == 0.0


def test_tfidf_similarity():
    text_a = "Apache HTTP Server vulnerability critical RCE"
    text_b = "Apache HTTP Server remote code execution vulnerability"
    score = tfidf_cosine_similarity(text_a, text_b)
    assert score > 0.3

    text_c = "Completely unrelated banking news about stocks"
    score2 = tfidf_cosine_similarity(text_a, text_c)
    assert score2 < score


@pytest.mark.asyncio
async def test_similarity_check_no_candidates(db_session):
    """With no candidates, should mark as not similar."""
    news = News(
        title="Unique News",
        url="https://example.com/unique-sim",
        title_zh="独特新闻",
        summary_zh="一条独特的新闻",
        category="其他",
        process_status=ProcessStatus.processed.value,
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    await check_similarity_for_news(db_session, news)
    assert news.is_similar is False


def test_parse_similarity_json_with_cleanup():
    raw = '```json\n{"is_similar": "否", "reason": "不是同一事件",}\n```'
    is_similar, reason = _parse_similarity_json(raw)
    assert is_similar is False
    assert "同一事件" in reason


@pytest.mark.asyncio
async def test_similarity_check_retry_on_parse_failure(db_session):
    news = News(
        title="CVE-2025-1234 in Microsoft Exchange exploited",
        url="https://example.com/sim-retry-news",
        summary="Attackers are actively exploiting CVE-2025-1234 in Microsoft Exchange.",
        category="重大漏洞风险提示",
        process_status=ProcessStatus.processed.value,
    )
    candidate = News(
        title="Microsoft Exchange faces active exploitation of CVE-2025-1234",
        url="https://example.com/sim-retry-candidate",
        summary="Security teams confirm in-the-wild exploitation for CVE-2025-1234.",
        category="重大漏洞风险提示",
        process_status=ProcessStatus.completed.value,
    )
    db_session.add(news)
    db_session.add(candidate)
    await db_session.commit()
    await db_session.refresh(news)
    await db_session.refresh(candidate)

    responses = [
        "相似: 是\n理由: 非JSON格式",
        '{"is_similar": true, "reason": "两条新闻描述同一漏洞与同一受影响产品"}',
    ]
    with patch(
        "app.services.similarity_checker.chat_completion",
        new_callable=AsyncMock,
        side_effect=responses,
    ) as mocked_completion:
        await check_similarity_for_news(db_session, news)

    assert mocked_completion.await_count == 2
    assert news.is_similar is True
    assert news.similar_to_id == candidate.id
    assert news.similarity_details is not None
    assert "llm_reason" in news.similarity_details


def test_parse_classification_json_with_cleanup():
    raw = '```json\n{"category": "重大网络安全事件",}\n```'
    category = _parse_classification_json(raw)
    assert category == "重大网络安全事件"


@pytest.mark.asyncio
async def test_classify_retry_on_parse_failure(db_session):
    responses = [
        "分类：重大漏洞风险提示",
        '{"category": "重大漏洞风险提示"}',
    ]
    with patch(
        "app.services.classifier.chat_completion",
        new_callable=AsyncMock,
        side_effect=responses,
    ) as mocked_completion:
        category = await classify_news(
            db_session,
            "Critical RCE found in Apache HTTP Server",
            "The vulnerability allows remote code execution without authentication.",
        )

    assert mocked_completion.await_count == 2
    assert category == "重大漏洞风险提示"


@pytest.mark.asyncio
async def test_classify_fallback_after_retry_failures(db_session):
    with patch(
        "app.services.classifier.chat_completion",
        new_callable=AsyncMock,
        side_effect=['{"category": "未知分类"}'] * 3,
    ) as mocked_completion:
        category = await classify_news(
            db_session,
            "Unknown topic title",
            "Unknown topic summary",
        )

    assert mocked_completion.await_count == 3
    assert category == "其他"


@pytest.mark.asyncio
async def test_importance_judge(db_session):
    """Test importance judgment with mocked LLM."""
    news = News(
        title="Critical Vuln",
        url="https://example.com/critical-importance",
        title_zh="严重漏洞",
        summary_zh="一个严重的漏洞",
        category="重大漏洞风险提示",
        process_status=ProcessStatus.similarity_checked.value,
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    with patch(
        "app.services.importance_judge.chat_completion",
        new_callable=AsyncMock,
        return_value='{"is_important": true, "reason": "严重RCE漏洞"}',
    ):
        await judge_importance_for_news(db_session, news)

    assert news.is_important is True
    assert "RCE" in news.importance_reason


def test_parse_importance_json_with_cleanup():
    raw = '```json\n{"is_important": "是", "reason": "高危漏洞已在野利用",}\n```'
    is_important, reason = _parse_importance_json(raw)
    assert is_important is True
    assert "在野利用" in reason


@pytest.mark.asyncio
async def test_importance_judge_retry_on_parse_failure(db_session):
    news = News(
        title="Retry Vuln",
        url="https://example.com/retry-importance",
        title_zh="需要重试的漏洞新闻",
        summary_zh="首次返回格式错误，第二次返回JSON",
        category="重大漏洞风险提示",
        process_status=ProcessStatus.similarity_checked.value,
    )
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    responses = [
        "重要: 是\n理由: 非JSON格式",
        '{"is_important": true, "reason": "修正后返回JSON"}',
    ]
    with patch(
        "app.services.importance_judge.chat_completion",
        new_callable=AsyncMock,
        side_effect=responses,
    ) as mocked_completion:
        await judge_importance_for_news(db_session, news)

    assert mocked_completion.await_count == 2
    assert news.is_important is True
    assert "JSON" in news.importance_reason


def test_scheduler_parse_cron():
    from app.services.scheduler import parse_cron
    result = parse_cron("0 */2 * * *")
    assert result["minute"] == "0"
    assert result["hour"] == "*/2"
