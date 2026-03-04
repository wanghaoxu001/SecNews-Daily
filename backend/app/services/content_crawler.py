import logging
import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
import time

from app.config import settings

logger = logging.getLogger(__name__)
WHITESPACE_RE = re.compile(r"\s+")

DEFAULT_WAIT_FOR_CHAIN = [
    "css:article, main, [role='main']",
    "css:main, body",
    "css:body",
]


@dataclass
class CrawlError:
    code: str
    message: str
    url: str
    exception_type: str | None = None
    retryable: bool = True

    def to_detail(self) -> str:
        detail = (
            f"crawl_error[{self.code}] {self.message} | "
            f"url={self.url} | retryable={self.retryable}"
        )
        if self.exception_type:
            detail += f" | exception={self.exception_type}"
        return detail


@dataclass
class CrawlAttemptConfig:
    page_timeout_ms: int
    wait_for: str


@dataclass
class CrawlResult:
    content: str | None
    error: CrawlError | None
    attempts: int
    total_duration_ms: int
    attempt_errors: list[CrawlError]


def format_crawl_error(error: CrawlError) -> str:
    return error.to_detail()


def format_crawl_result_detail(result: CrawlResult) -> str:
    if result.error:
        chain = ">".join(err.code for err in result.attempt_errors) if result.attempt_errors else result.error.code
        return (
            f"{result.error.to_detail()} | attempts={result.attempts} | "
            f"total_duration_ms={result.total_duration_ms} | error_chain={chain}"
        )
    return f"crawl_success | attempts={result.attempts} | total_duration_ms={result.total_duration_ms}"


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return WHITESPACE_RE.sub(" ", text).strip()


def _truncate_text(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len]


def _to_positive_int(value: Any, default: int) -> int:
    if isinstance(value, int) and value > 0:
        return value
    return default


def _to_non_negative_int(value: Any, default: int) -> int:
    if isinstance(value, int) and value >= 0:
        return value
    return default


def _classify_crawl_error(
    *,
    url: str,
    message: str,
    exception_type: str | None = None,
) -> CrawlError:
    lowered = message.lower()

    if "executable doesn't exist" in lowered or "browsertype.launch" in lowered:
        return CrawlError(
            code="BROWSER_MISSING",
            message="Playwright browser executable is missing",
            url=url,
            exception_type=exception_type,
            retryable=False,
        )
    if "timeout" in lowered:
        return CrawlError(
            code="NAV_TIMEOUT",
            message="Navigation timed out during crawling",
            url=url,
            exception_type=exception_type,
            retryable=True,
        )
    if "403" in lowered or "429" in lowered or "forbidden" in lowered:
        return CrawlError(
            code="ACCESS_DENIED",
            message="Access denied by target site",
            url=url,
            exception_type=exception_type,
            retryable=True,
        )
    if "captcha" in lowered or "challenge" in lowered or "cf-chl" in lowered:
        return CrawlError(
            code="BLOCKED_OR_CHALLENGE",
            message="Crawler challenged by anti-bot protection",
            url=url,
            exception_type=exception_type,
            retryable=True,
        )

    compact = message.strip() or "Unexpected crawler exception"
    return CrawlError(
        code="CRAWLER_EXCEPTION",
        message=compact[:200],
        url=url,
        exception_type=exception_type,
        retryable=True,
    )


def _build_browser_config(BrowserConfig: Any) -> Any:
    # Some Crawl4AI versions expose different BrowserConfig kwargs.
    full_kwargs = {
        "browser_type": settings.CRAWL_BROWSER_TYPE,
        "headless": settings.CRAWL_HEADLESS,
        "text_mode": True,
        "user_agent": settings.CRAWL_USER_AGENT,
        "extra_args": ["--no-sandbox"],
        "verbose": False,
    }
    try:
        return BrowserConfig(**full_kwargs)
    except TypeError:
        fallback_kwargs = {
            "browser_type": settings.CRAWL_BROWSER_TYPE,
            "headless": settings.CRAWL_HEADLESS,
        }
        return BrowserConfig(**fallback_kwargs)


def _build_run_config(
    CrawlerRunConfig: Any,
    CacheMode: Any,
    *,
    page_timeout_ms: int,
    wait_for: str,
    simulate_user: bool,
    magic: bool,
) -> Any:
    cache_bypass = getattr(CacheMode, "BYPASS", "BYPASS")
    full_kwargs = {
        "cache_mode": cache_bypass,
        "page_timeout": page_timeout_ms,
        "word_count_threshold": 20,
        "wait_for": wait_for,
        "remove_overlay_elements": True,
        "simulate_user": simulate_user,
        "magic": magic,
        "check_robots_txt": settings.CRAWL_CHECK_ROBOTS,
    }
    try:
        return CrawlerRunConfig(**full_kwargs)
    except TypeError:
        fallback_kwargs = {
            "cache_mode": cache_bypass,
            "page_timeout": page_timeout_ms,
        }
        try:
            return CrawlerRunConfig(**fallback_kwargs)
        except TypeError:
            return CrawlerRunConfig()


def _extract_content(result: Any) -> str:
    markdown = _normalize_text(getattr(result, "markdown", None))
    if markdown:
        return markdown
    return _normalize_text(getattr(result, "cleaned_html", None))


def _load_domain_overrides() -> dict[str, dict[str, Any]]:
    raw = (settings.CRAWL_DOMAIN_OVERRIDES_JSON or "").strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Invalid CRAWL_DOMAIN_OVERRIDES_JSON: %s", exc)
        return {}

    if not isinstance(payload, dict):
        logger.warning("CRAWL_DOMAIN_OVERRIDES_JSON must be a JSON object")
        return {}

    overrides: dict[str, dict[str, Any]] = {}
    for host, cfg in payload.items():
        if isinstance(host, str) and host and isinstance(cfg, dict):
            overrides[host.lower()] = cfg
    return overrides


def _build_default_timeouts(attempt_count: int) -> list[int]:
    base = _to_positive_int(settings.CRAWL_PAGE_TIMEOUT_MS, 45000)
    values = [base, max(base, 75000), max(base, 90000)]
    while len(values) < attempt_count:
        values.append(values[-1] + 15000)
    return values[:attempt_count]


def _normalize_timeout_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    normalized = [_to_positive_int(v, -1) for v in value]
    return [v for v in normalized if v > 0]


def _normalize_wait_for_list(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, list):
        waits = [v.strip() for v in value if isinstance(v, str) and v.strip()]
        return waits
    return []


def _build_attempt_plan(url: str) -> tuple[list[CrawlAttemptConfig], dict[str, Any]]:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    override = _load_domain_overrides().get(host, {})

    max_retries = _to_non_negative_int(settings.CRAWL_MAX_RETRIES, 2)
    override_retries = override.get("max_retries")
    if isinstance(override_retries, int) and override_retries >= 0:
        max_retries = override_retries
    attempt_count = max_retries + 1

    default_timeouts = _build_default_timeouts(attempt_count)
    timeout_values = _normalize_timeout_list(override.get("timeouts_ms")) or default_timeouts
    while len(timeout_values) < attempt_count:
        timeout_values.append(timeout_values[-1])
    timeout_values = timeout_values[:attempt_count]

    default_waits = [settings.CRAWL_WAIT_FOR or DEFAULT_WAIT_FOR_CHAIN[0]] + DEFAULT_WAIT_FOR_CHAIN[1:]
    while len(default_waits) < attempt_count:
        default_waits.append(default_waits[-1])
    wait_values = _normalize_wait_for_list(override.get("wait_for")) or default_waits
    while len(wait_values) < attempt_count:
        wait_values.append(wait_values[-1])
    wait_values = wait_values[:attempt_count]

    plan = [
        CrawlAttemptConfig(page_timeout_ms=timeout_values[i], wait_for=wait_values[i])
        for i in range(attempt_count)
    ]
    return plan, override


def _get_override_bool(override: dict[str, Any], key: str, default: bool) -> bool:
    value = override.get(key)
    return value if isinstance(value, bool) else default


async def crawl_article_content_with_meta(url: str) -> CrawlResult:
    """Crawl article full text using Crawl4AI and return structured result."""
    started = time.monotonic()
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
    except ModuleNotFoundError:
        error = CrawlError(
            code="BROWSER_MISSING",
            message="crawl4ai runtime not available",
            url=url,
            exception_type="ModuleNotFoundError",
            retryable=False,
        )
        logger.warning("Failed to crawl %s: %s", url, error.to_detail())
        total_duration_ms = int((time.monotonic() - started) * 1000)
        return CrawlResult(None, error, attempts=1, total_duration_ms=total_duration_ms, attempt_errors=[error])
    except Exception as exc:  # pragma: no cover - defensive mapping
        error = _classify_crawl_error(
            url=url,
            message=str(exc),
            exception_type=type(exc).__name__,
        )
        logger.warning("Failed to crawl %s: %s", url, error.to_detail())
        total_duration_ms = int((time.monotonic() - started) * 1000)
        return CrawlResult(None, error, attempts=1, total_duration_ms=total_duration_ms, attempt_errors=[error])

    attempt_plan, override = _build_attempt_plan(url)
    attempt_errors: list[CrawlError] = []
    simulate_user = _get_override_bool(override, "simulate_user", settings.CRAWL_SIMULATE_USER)
    magic = _get_override_bool(override, "magic", settings.CRAWL_MAGIC)

    try:
        browser_config = _build_browser_config(BrowserConfig)
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for idx, attempt in enumerate(attempt_plan, start=1):
                try:
                    run_config = _build_run_config(
                        CrawlerRunConfig,
                        CacheMode,
                        page_timeout_ms=attempt.page_timeout_ms,
                        wait_for=attempt.wait_for,
                        simulate_user=simulate_user,
                        magic=magic,
                    )
                    result = await crawler.arun(url=url, config=run_config)
                except Exception as exc:
                    error = _classify_crawl_error(
                        url=url,
                        message=str(exc),
                        exception_type=type(exc).__name__,
                    )
                    attempt_errors.append(error)
                    logger.warning(
                        "Crawl attempt %s/%s failed for %s: %s",
                        idx,
                        len(attempt_plan),
                        url,
                        error.to_detail(),
                    )
                    if error.retryable and idx < len(attempt_plan):
                        continue
                    total_duration_ms = int((time.monotonic() - started) * 1000)
                    return CrawlResult(
                        None,
                        error,
                        attempts=idx,
                        total_duration_ms=total_duration_ms,
                        attempt_errors=attempt_errors,
                    )

                if not getattr(result, "success", False):
                    error_message = getattr(result, "error_message", "") or "crawl4ai returned unsuccessful result"
                    error = _classify_crawl_error(url=url, message=error_message)
                    attempt_errors.append(error)
                    logger.warning(
                        "Crawl attempt %s/%s failed for %s: %s",
                        idx,
                        len(attempt_plan),
                        url,
                        error.to_detail(),
                    )
                    if error.retryable and idx < len(attempt_plan):
                        continue
                    total_duration_ms = int((time.monotonic() - started) * 1000)
                    return CrawlResult(
                        None,
                        error,
                        attempts=idx,
                        total_duration_ms=total_duration_ms,
                        attempt_errors=attempt_errors,
                    )

                content = _extract_content(result)
                if len(content) < settings.CRAWL_MIN_CONTENT_LEN:
                    error = CrawlError(
                        code="EMPTY_CONTENT",
                        message=f"Crawler returned short content ({len(content)} chars)",
                        url=url,
                        retryable=False,
                    )
                    attempt_errors.append(error)
                    logger.info("Crawler returned insufficient content for %s: %s", url, error.to_detail())
                    total_duration_ms = int((time.monotonic() - started) * 1000)
                    return CrawlResult(
                        None,
                        error,
                        attempts=idx,
                        total_duration_ms=total_duration_ms,
                        attempt_errors=attempt_errors,
                    )

                content = _truncate_text(content, settings.CRAWL_MAX_CONTENT_LEN)
                total_duration_ms = int((time.monotonic() - started) * 1000)
                return CrawlResult(
                    content,
                    None,
                    attempts=idx,
                    total_duration_ms=total_duration_ms,
                    attempt_errors=attempt_errors,
                )
    except Exception as exc:
        error = _classify_crawl_error(
            url=url,
            message=str(exc),
            exception_type=type(exc).__name__,
        )
        attempt_errors.append(error)
        logger.warning("Failed to crawl %s: %s", url, error.to_detail())
        total_duration_ms = int((time.monotonic() - started) * 1000)
        return CrawlResult(
            None,
            error,
            attempts=1,
            total_duration_ms=total_duration_ms,
            attempt_errors=attempt_errors,
        )


async def crawl_article_content(url: str) -> str | None:
    result = await crawl_article_content_with_meta(url)
    return result.content
