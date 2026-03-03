import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from sqlalchemy import select

from app.models.rss_source import RssSource
from app.models.news import News
from app.services.rss_fetcher import fetch_all_sources, fetch_single_source, _parse_feed


def _make_feed_entry(title, url, summary="", content=None, author="", description="", extra=None):
    entry = MagicMock()
    values = {
        "title": title,
        "link": url,
        "summary": summary,
        "description": description,
        "content": content or [],
        "author": author,
    }
    if extra:
        values.update(extra)
    entry.get = lambda k, d="": values.get(k, d)
    entry.title = title
    entry.published_parsed = (2025, 1, 15, 10, 0, 0, 0, 0, 0)
    return entry


def test_parse_feed_extracts_and_cleans_summary_content():
    fake_feed = MagicMock()
    fake_feed.entries = [
        _make_feed_entry(
            "Article 1",
            "https://example.com/1",
            summary="<p>Summary <b>text</b></p>",
            content=[{"value": "<div>Full <b>content</b> &amp; details</div>"}],
            author="Alice",
        ),
    ]

    with patch("app.services.rss_fetcher.feedparser.parse", return_value=fake_feed):
        entries = _parse_feed("https://example.com/rss")

    assert len(entries) == 1
    assert entries[0]["summary"] == "Summary text"
    assert entries[0]["content"] == "Full content & details"
    assert entries[0]["author"] == "Alice"


def test_parse_feed_fallbacks_to_content_encoded():
    fake_feed = MagicMock()
    fake_feed.entries = [
        _make_feed_entry(
            "Article 2",
            "https://example.com/2",
            summary="",
            content=[],
            extra={"content:encoded": "<article>Encoded <i>body</i></article>"},
        ),
    ]

    with patch("app.services.rss_fetcher.feedparser.parse", return_value=fake_feed):
        entries = _parse_feed("https://example.com/rss")

    assert len(entries) == 1
    assert entries[0]["content"] == "Encoded body"


@pytest.mark.asyncio
async def test_fetch_rss_creates_news(db_session):
    # Insert an RSS source
    source = RssSource(name="Test Feed", url="https://example.com/rss", enabled=True)
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    fake_feed = MagicMock()
    fake_feed.entries = [
        _make_feed_entry("Article 1", "https://example.com/1", "Summary 1"),
        _make_feed_entry("Article 2", "https://example.com/2", "Summary 2"),
    ]

    with patch("app.services.rss_fetcher._parse_feed", return_value=[
        {"title": "Article 1", "url": "https://example.com/1", "summary": "Summary 1", "content": "Content 1", "author": "", "published_at": datetime(2025, 1, 15, tzinfo=timezone.utc)},
        {"title": "Article 2", "url": "https://example.com/2", "summary": "Summary 2", "content": "Content 2", "author": "", "published_at": datetime(2025, 1, 15, tzinfo=timezone.utc)},
    ]):
        result = await fetch_all_sources(db_session)

    assert result["total_new"] == 2
    assert result["sources_processed"] == 1
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_fetch_rss_deduplicates(db_session):
    source = RssSource(name="Test Feed 2", url="https://example.com/rss2", enabled=True)
    db_session.add(source)
    await db_session.commit()

    # Pre-insert a news item
    existing = News(title="Old", url="https://example.com/dup", process_status="pending")
    db_session.add(existing)
    await db_session.commit()
    await db_session.refresh(source)

    with patch("app.services.rss_fetcher._parse_feed", return_value=[
        {"title": "Dup", "url": "https://example.com/dup", "summary": "", "content": "", "author": "", "published_at": None},
        {"title": "New", "url": "https://example.com/new", "summary": "", "content": "", "author": "", "published_at": None},
    ]):
        count = await fetch_single_source(db_session, source)

    assert count == 1  # only the new one


@pytest.mark.asyncio
async def test_fetch_rss_persists_content_field(db_session):
    source = RssSource(name="Content Feed", url="https://example.com/rss-content", enabled=True)
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    with patch("app.services.rss_fetcher._parse_feed", return_value=[
        {
            "title": "Content Article",
            "url": "https://example.com/content-1",
            "summary": "",
            "content": "Full body from RSS content field",
            "author": "Bob",
            "published_at": datetime(2025, 1, 15, tzinfo=timezone.utc),
        },
    ]):
        count = await fetch_single_source(db_session, source)

    assert count == 1
    result = await db_session.execute(select(News).where(News.url == "https://example.com/content-1"))
    saved = result.scalar_one()
    assert saved.content == "Full body from RSS content field"
    assert saved.summary is None


@pytest.mark.asyncio
async def test_fetch_rss_single_source_failure_isolated(db_session):
    source = RssSource(name="Bad Feed", url="https://bad.example.com/rss", enabled=True)
    db_session.add(source)
    await db_session.commit()

    with patch("app.services.rss_fetcher._parse_feed", side_effect=Exception("Network error")):
        result = await fetch_all_sources(db_session)

    assert result["total_new"] == 0
    assert result["sources_processed"] == 1  # at least some sources in db from prev tests


@pytest.mark.asyncio
async def test_news_list_api(client, auth_headers, db_session):
    # Insert test news
    news = News(title="Test News", url="https://example.com/test-api", process_status="pending")
    db_session.add(news)
    await db_session.commit()

    resp = await client.get("/api/v1/news", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_news_detail_api(client, auth_headers, db_session):
    news = News(title="Detail Test", url="https://example.com/detail-test", process_status="pending")
    db_session.add(news)
    await db_session.commit()
    await db_session.refresh(news)

    resp = await client.get(f"/api/v1/news/{news.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Detail Test"

    resp = await client.get("/api/v1/news/99999", headers=auth_headers)
    assert resp.status_code == 404
