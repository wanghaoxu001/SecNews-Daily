import asyncio
import logging
import statistics
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.models.crawl_domain_policy import CrawlDomainPolicy
from app.models.rss_source import RssSource
from app.services.content_crawler import (
    crawl_article_content_with_meta,
    extract_domain_from_url,
    get_domain_policy_snapshot,
    get_effective_domain_policy,
    invalidate_domain_policy_cache,
)
from app.services.rss_fetcher import _parse_feed

logger = logging.getLogger(__name__)


_PROBE_LOCKS: dict[str, asyncio.Lock] = {}


def _get_probe_lock(domain: str) -> asyncio.Lock:
    lock = _PROBE_LOCKS.get(domain)
    if lock is None:
        lock = asyncio.Lock()
        _PROBE_LOCKS[domain] = lock
    return lock


def _to_positive_int(value: Any, default: int) -> int:
    if isinstance(value, int) and value > 0:
        return value
    return default


def _build_probe_candidates() -> list[dict[str, Any]]:
    base = _to_positive_int(settings.CRAWL_PAGE_TIMEOUT_MS, 45000)
    return [
        {
            "timeouts_ms": [base, max(base, 75000), max(base, 90000)],
            "wait_for": ["css:main, body", "css:body", "css:body"],
        },
        {
            "timeouts_ms": [base, max(base, 75000), max(base, 90000)],
            "wait_for": ["css:article, main, [role='main']", "css:main, body", "css:body"],
        },
        {
            "timeouts_ms": [base, max(base, 75000), max(base, 90000)],
            "wait_for": ["css:body", "css:body", "css:body"],
        },
    ]


async def _load_sample_urls(source: RssSource, sample_size: int) -> list[str]:
    loop = asyncio.get_running_loop()
    entries = await loop.run_in_executor(None, _parse_feed, source.url)
    urls: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        url = (entry.get("url") or "").strip()
        if not url or not url.startswith(("http://", "https://")):
            continue
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)
        if len(urls) >= sample_size:
            break
    return urls


async def _evaluate_candidate(
    *,
    sample_urls: list[str],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    sem = asyncio.Semaphore(_to_positive_int(settings.CRAWL_POLICY_PROBE_CONCURRENCY, 2))

    async def run_one(url: str):
        async with sem:
            return await crawl_article_content_with_meta(url, policy_override=candidate)

    results = await asyncio.gather(*(run_one(url) for url in sample_urls))
    success_count = 0
    first_try_count = 0
    durations: list[int] = []
    content_lengths: list[int] = []

    for item in results:
        durations.append(item.total_duration_ms)
        content_len = len(item.content or "")
        if item.error is None and content_len >= settings.CRAWL_MIN_CONTENT_LEN:
            success_count += 1
            content_lengths.append(content_len)
            if item.attempts == 1:
                first_try_count += 1

    sample_size = len(sample_urls)
    success_rate = success_count / sample_size if sample_size else 0.0
    first_try_rate = first_try_count / sample_size if sample_size else 0.0
    avg_duration_ms = int(statistics.mean(durations)) if durations else 0
    avg_content_len = int(statistics.mean(content_lengths)) if content_lengths else 0

    return {
        "candidate": candidate,
        "success_rate": success_rate,
        "first_try_rate": first_try_rate,
        "avg_duration_ms": avg_duration_ms,
        "avg_content_len": avg_content_len,
    }


def _candidate_score(payload: dict[str, Any]) -> tuple[float, float, float, int]:
    return (
        payload["success_rate"],
        payload["first_try_rate"],
        -float(payload["avg_duration_ms"]),
        int(payload["avg_content_len"]),
    )


async def _get_or_create_policy(db: AsyncSession, domain: str) -> CrawlDomainPolicy:
    result = await db.execute(select(CrawlDomainPolicy).where(CrawlDomainPolicy.domain == domain))
    policy = result.scalar_one_or_none()
    if policy:
        return policy
    policy = CrawlDomainPolicy(domain=domain, probe_status="pending")
    db.add(policy)
    await db.flush()
    return policy


async def get_policy_response_by_domain(db: AsyncSession, domain: str) -> dict[str, Any] | None:
    domain = domain.strip().lower()
    if not domain:
        return None
    snapshot = await get_domain_policy_snapshot(domain, db)
    if snapshot is None:
        return None
    effective = await get_effective_domain_policy(domain, db=db)
    return {
        **snapshot,
        "effective_wait_for_chain": effective["wait_for_chain"],
        "effective_timeouts_ms": effective["timeouts_ms"],
        "effective_source": effective["source"],
    }


async def probe_domain_policy_for_source(db: AsyncSession, source: RssSource) -> dict[str, Any]:
    domain = extract_domain_from_url(source.url)
    if not domain:
        raise ValueError("Invalid source url: cannot resolve domain")

    lock = _get_probe_lock(domain)
    async with lock:
        policy = await _get_or_create_policy(db, domain)
        policy.probe_status = "running"
        policy.probe_last_error = None
        policy.probe_last_run_at = datetime.now(timezone.utc)
        await db.commit()

        sample_size = _to_positive_int(settings.CRAWL_POLICY_PROBE_SAMPLE_SIZE, 3)
        sample_urls = await _load_sample_urls(source, sample_size)
        if not sample_urls:
            policy = await _get_or_create_policy(db, domain)
            policy.probe_status = "failed"
            policy.probe_sample_size = 0
            policy.probe_success_rate = 0
            policy.probe_avg_duration_ms = None
            policy.probe_last_error = "No sample article URLs found from RSS feed"
            policy.probe_last_run_at = datetime.now(timezone.utc)
            await db.commit()
            invalidate_domain_policy_cache(domain)
            payload = await get_policy_response_by_domain(db, domain)
            if payload is None:
                raise RuntimeError("Probe completed but no crawl policy row found")
            return payload

        candidates = _build_probe_candidates()
        candidate_results: list[dict[str, Any]] = []
        for candidate in candidates:
            candidate_results.append(await _evaluate_candidate(sample_urls=sample_urls, candidate=candidate))

        best = max(candidate_results, key=_candidate_score)
        policy = await _get_or_create_policy(db, domain)
        policy.probe_sample_size = len(sample_urls)
        policy.probe_success_rate = best["success_rate"]
        policy.probe_avg_duration_ms = best["avg_duration_ms"]
        policy.probe_last_run_at = datetime.now(timezone.utc)

        if best["success_rate"] > 0:
            policy.wait_for_chain = best["candidate"]["wait_for"]
            policy.timeouts_ms = best["candidate"]["timeouts_ms"]
            policy.probe_status = "success"
            policy.probe_last_error = None
        else:
            policy.probe_status = "failed"
            policy.probe_last_error = "All candidate wait_for strategies failed on sampled URLs"

        await db.commit()
        invalidate_domain_policy_cache(domain)

        payload = await get_policy_response_by_domain(db, domain)
        if payload is None:
            raise RuntimeError("Probe completed but no crawl policy row found")
        return payload


async def probe_domain_policy_for_source_id(source_id: int) -> None:
    if not settings.CRAWL_POLICY_PROBE_ENABLED:
        return

    try:
        async with async_session() as db:
            source = await db.get(RssSource, source_id)
            if source is None:
                return
            await probe_domain_policy_for_source(db, source)
    except Exception as exc:  # pragma: no cover - async background fallback
        logger.warning("Auto probe failed for source_id=%s: %s", source_id, exc)
