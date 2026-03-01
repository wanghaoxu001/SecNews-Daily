import logging

logger = logging.getLogger(__name__)


async def crawl_article_content(url: str) -> str | None:
    """Crawl article full text using Crawl4AI. Returns markdown content or None."""
    try:
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            if result.success and result.markdown:
                # Truncate to avoid huge content
                return result.markdown[:5000]
            return None
    except Exception as e:
        logger.warning(f"Failed to crawl {url}: {e}")
        return None
