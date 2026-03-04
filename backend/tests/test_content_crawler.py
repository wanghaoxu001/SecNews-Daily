import sys
from types import ModuleType, SimpleNamespace

import pytest

from app.config import settings
from app.services.content_crawler import crawl_article_content, crawl_article_content_with_meta


def _install_fake_crawl4ai(monkeypatch, *, responses: list[object]) -> list[dict]:
    module = ModuleType("crawl4ai")
    calls: list[dict] = []
    queue = list(responses)

    class BrowserConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class CrawlerRunConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class CacheMode:
        BYPASS = "BYPASS"

    class AsyncWebCrawler:
        def __init__(self, config=None):
            self.config = config

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def arun(self, url: str, config=None):
            calls.append({"url": url, "config": config})
            if queue:
                item = queue.pop(0)
            else:
                item = SimpleNamespace(
                    success=True,
                    markdown="fallback content " * 50,
                    cleaned_html="",
                    error_message="",
                )
            if isinstance(item, Exception):
                raise item
            return item

    module.AsyncWebCrawler = AsyncWebCrawler
    module.BrowserConfig = BrowserConfig
    module.CrawlerRunConfig = CrawlerRunConfig
    module.CacheMode = CacheMode
    monkeypatch.setitem(sys.modules, "crawl4ai", module)
    return calls


@pytest.mark.asyncio
async def test_crawl_article_content_success_truncates_content(monkeypatch):
    monkeypatch.setattr(settings, "CRAWL_MAX_RETRIES", 2)
    monkeypatch.setattr(settings, "CRAWL_DOMAIN_OVERRIDES_JSON", "{}")
    long_markdown = "A" * (settings.CRAWL_MAX_CONTENT_LEN + 800)
    result = SimpleNamespace(success=True, markdown=long_markdown, cleaned_html="", error_message="")
    calls = _install_fake_crawl4ai(monkeypatch, responses=[result, result])

    crawl_result = await crawl_article_content_with_meta("https://example.com/article")
    wrapped = await crawl_article_content("https://example.com/article")

    assert crawl_result.error is None
    assert crawl_result.content is not None
    assert len(crawl_result.content) == settings.CRAWL_MAX_CONTENT_LEN
    assert crawl_result.attempts == 1
    assert wrapped == crawl_result.content
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_crawl_article_content_maps_browser_missing(monkeypatch):
    monkeypatch.setattr(settings, "CRAWL_MAX_RETRIES", 2)
    _install_fake_crawl4ai(
        monkeypatch,
        responses=[RuntimeError("BrowserType.launch: Executable doesn't exist at /path/chrome")],
    )

    result = await crawl_article_content_with_meta("https://example.com/article")

    assert result.content is None
    assert result.error is not None
    assert result.error.code == "BROWSER_MISSING"
    assert result.error.retryable is False
    assert result.attempts == 1


@pytest.mark.asyncio
async def test_crawl_article_content_retries_timeout_then_succeeds(monkeypatch):
    monkeypatch.setattr(settings, "CRAWL_MAX_RETRIES", 2)
    calls = _install_fake_crawl4ai(
        monkeypatch,
        responses=[
            TimeoutError("Navigation timeout of 30000 ms exceeded"),
            SimpleNamespace(success=True, markdown="valid content " * 40, cleaned_html="", error_message=""),
        ],
    )

    result = await crawl_article_content_with_meta("https://example.com/article")

    assert result.error is None
    assert result.content is not None
    assert result.attempts == 2
    assert len(result.attempt_errors) == 1
    assert result.attempt_errors[0].code == "NAV_TIMEOUT"
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_crawl_article_content_maps_short_content(monkeypatch):
    monkeypatch.setattr(settings, "CRAWL_MAX_RETRIES", 2)
    result = SimpleNamespace(success=True, markdown="short", cleaned_html="", error_message="")
    _install_fake_crawl4ai(monkeypatch, responses=[result])

    crawl_result = await crawl_article_content_with_meta("https://example.com/article")

    assert crawl_result.content is None
    assert crawl_result.error is not None
    assert crawl_result.error.code == "EMPTY_CONTENT"
    assert crawl_result.error.retryable is False


@pytest.mark.asyncio
async def test_crawl_article_content_maps_unsuccessful_result(monkeypatch):
    monkeypatch.setattr(settings, "CRAWL_MAX_RETRIES", 0)
    result = SimpleNamespace(
        success=False,
        markdown="",
        cleaned_html="",
        error_message="HTTP 403 Forbidden",
    )
    _install_fake_crawl4ai(monkeypatch, responses=[result])

    crawl_result = await crawl_article_content_with_meta("https://example.com/article")

    assert crawl_result.content is None
    assert crawl_result.error is not None
    assert crawl_result.error.code == "ACCESS_DENIED"
    assert crawl_result.attempts == 1


@pytest.mark.asyncio
async def test_crawl_article_content_applies_domain_override(monkeypatch):
    monkeypatch.setattr(settings, "CRAWL_MAX_RETRIES", 2)
    monkeypatch.setattr(
        settings,
        "CRAWL_DOMAIN_OVERRIDES_JSON",
        '{"www.bleepingcomputer.com":{"timeouts_ms":[71000,91000,121000],"wait_for":["css:main","css:body","css:body"]}}',
    )
    calls = _install_fake_crawl4ai(
        monkeypatch,
        responses=[
            TimeoutError("Navigation timeout of 30000 ms exceeded"),
            TimeoutError("Navigation timeout of 30000 ms exceeded"),
            SimpleNamespace(success=True, markdown="valid content " * 40, cleaned_html="", error_message=""),
        ],
    )

    result = await crawl_article_content_with_meta(
        "https://www.bleepingcomputer.com/news/security/lexisnexis-confirms-data-breach-as-hackers-leak-stolen-files/"
    )

    assert result.error is None
    assert result.attempts == 3
    assert len(calls) == 3
    assert calls[0]["config"].kwargs["page_timeout"] == 71000
    assert calls[1]["config"].kwargs["page_timeout"] == 91000
    assert calls[2]["config"].kwargs["page_timeout"] == 121000
    assert calls[0]["config"].kwargs["wait_for"] == "css:main"
    assert calls[1]["config"].kwargs["wait_for"] == "css:body"
