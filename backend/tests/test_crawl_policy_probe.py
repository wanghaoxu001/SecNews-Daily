from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.config import settings
from app.models.crawl_domain_policy import CrawlDomainPolicy
from app.models.rss_source import RssSource
from app.services.content_crawler import CrawlError, CrawlResult
from app.services.crawl_policy_probe import probe_domain_policy_for_source


def _success_result(*, attempts: int, duration_ms: int) -> CrawlResult:
    return CrawlResult(
        content="valid content " * 40,
        error=None,
        attempts=attempts,
        total_duration_ms=duration_ms,
        attempt_errors=[],
    )


def _failed_result(url: str) -> CrawlResult:
    err = CrawlError(
        code="NAV_TIMEOUT",
        message="Navigation timed out during crawling",
        url=url,
        retryable=True,
    )
    return CrawlResult(
        content=None,
        error=err,
        attempts=1,
        total_duration_ms=45000,
        attempt_errors=[err],
    )


@pytest.mark.asyncio
async def test_probe_domain_policy_selects_fastest_success_strategy(db_session, monkeypatch):
    monkeypatch.setattr(settings, "CRAWL_POLICY_PROBE_ENABLED", True)
    monkeypatch.setattr(settings, "CRAWL_POLICY_PROBE_SAMPLE_SIZE", 3)
    monkeypatch.setattr(settings, "CRAWL_POLICY_PROBE_CONCURRENCY", 2)

    source = RssSource(name="Probe Source", url="https://example.com/rss")
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    monkeypatch.setattr(
        "app.services.crawl_policy_probe._load_sample_urls",
        AsyncMock(return_value=[
            "https://example.com/a",
            "https://example.com/b",
            "https://example.com/c",
        ]),
    )

    async def fake_crawl(url: str, *, policy_override=None):
        first_wait = (policy_override or {}).get("wait_for", [""])[0]
        if first_wait == "css:main, body":
            return _success_result(attempts=1, duration_ms=5200)
        if first_wait == "css:article, main, [role='main']":
            return _success_result(attempts=2, duration_ms=9800)
        return _failed_result(url)

    monkeypatch.setattr("app.services.crawl_policy_probe.crawl_article_content_with_meta", fake_crawl)

    payload = await probe_domain_policy_for_source(db_session, source)

    assert payload["domain"] == "example.com"
    assert payload["probe_status"] == "success"
    assert payload["wait_for_chain"] == ["css:main, body", "css:body", "css:body"]
    assert payload["effective_source"] == "db"

    row = (
        await db_session.execute(select(CrawlDomainPolicy).where(CrawlDomainPolicy.domain == "example.com"))
    ).scalar_one()
    assert row.probe_status == "success"
    assert row.wait_for_chain == ["css:main, body", "css:body", "css:body"]


@pytest.mark.asyncio
async def test_probe_domain_policy_marks_failed_when_no_samples(db_session, monkeypatch):
    monkeypatch.setattr(settings, "CRAWL_POLICY_PROBE_ENABLED", True)
    source = RssSource(name="Probe Source Empty", url="https://empty.example.com/rss")
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    monkeypatch.setattr("app.services.crawl_policy_probe._load_sample_urls", AsyncMock(return_value=[]))

    payload = await probe_domain_policy_for_source(db_session, source)

    assert payload["probe_status"] == "failed"
    assert payload["probe_last_error"] == "No sample article URLs found from RSS feed"
