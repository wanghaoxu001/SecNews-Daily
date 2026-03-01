import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.database import async_session
from app.models.task_config import TaskConfig
from app.services.pipeline_orchestrator import run_full_pipeline
from app.services.rss_fetcher import fetch_all_sources
from app.services.news_processor import process_pending_news
from app.services.similarity_checker import check_similarity_batch
from app.services.importance_judge import judge_importance_batch

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

TASK_FUNC_MAP = {
    "fetch_rss": fetch_all_sources,
    "process_news": process_pending_news,
    "check_similarity": check_similarity_batch,
    "judge_importance": judge_importance_batch,
    "full_pipeline": run_full_pipeline,
}


async def _run_task(task_name: str):
    func = TASK_FUNC_MAP.get(task_name)
    if not func:
        logger.error(f"Unknown task: {task_name}")
        return
    async with async_session() as db:
        try:
            result = await func(db)
            logger.info(f"Task {task_name} completed: {result}")
        except Exception as e:
            logger.error(f"Task {task_name} failed: {e}")


def parse_cron(expr: str) -> dict:
    """Parse cron expression '* * * * *' to APScheduler kwargs."""
    parts = expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {expr}")
    return {
        "minute": parts[0],
        "hour": parts[1],
        "day": parts[2],
        "month": parts[3],
        "day_of_week": parts[4],
    }


async def load_scheduled_tasks():
    """Load task configs from DB and register with scheduler."""
    async with async_session() as db:
        result = await db.execute(select(TaskConfig).where(TaskConfig.enabled == True))
        configs = result.scalars().all()

    for config in configs:
        try:
            cron_kwargs = parse_cron(config.cron_expression)
            scheduler.add_job(
                _run_task,
                "cron",
                args=[config.name],
                id=f"task_{config.name}",
                replace_existing=True,
                **cron_kwargs,
            )
            logger.info(f"Scheduled task: {config.name} with cron {config.cron_expression}")
        except Exception as e:
            logger.error(f"Failed to schedule task {config.name}: {e}")


async def start_scheduler():
    await load_scheduled_tasks()
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler stopped")
