import pytest
from unittest.mock import patch, AsyncMock

from app.models.news import News
from app.models.enums import ProcessStatus
from app.services.entity_extractor import extract_entities, entity_overlap_score
from app.services.keyword_analyzer import tfidf_cosine_similarity
from app.services.similarity_checker import check_similarity_for_news
from app.services.importance_judge import judge_importance_for_news, SampleBasedStrategy


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

    with patch("app.services.importance_judge.chat_completion", new_callable=AsyncMock, return_value="重要: 是\n理由: 严重RCE漏洞"):
        await judge_importance_for_news(db_session, news)

    assert news.is_important is True
    assert "RCE" in news.importance_reason


def test_scheduler_parse_cron():
    from app.services.scheduler import parse_cron
    result = parse_cron("0 */2 * * *")
    assert result["minute"] == "0"
    assert result["hour"] == "*/2"
