import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rss_fetcher import fetch_all_sources
from app.services.news_processor import process_pending_news
from app.services.similarity_checker import check_similarity_batch
from app.services.importance_judge import judge_importance_batch

logger = logging.getLogger(__name__)


async def run_full_pipeline(db: AsyncSession) -> dict:
    """Run the complete pipeline: fetch → process → similarity → importance."""
    results = {}

    logger.info("Pipeline Step 1: Fetching RSS")
    results["fetch"] = await fetch_all_sources(db)

    logger.info("Pipeline Step 2: Processing news")
    results["process"] = await process_pending_news(db)

    logger.info("Pipeline Step 3: Checking similarity")
    results["similarity"] = await check_similarity_batch(db)

    logger.info("Pipeline Step 4: Judging importance")
    results["importance"] = await judge_importance_batch(db)

    logger.info("Pipeline complete")
    return results
