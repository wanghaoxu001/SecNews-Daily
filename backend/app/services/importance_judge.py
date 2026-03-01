import logging
from abc import ABC, abstractmethod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import News
from app.models.enums import ProcessStatus
from app.models.importance_example import ImportanceExample
from app.services.llm_client import chat_completion
from app.prompts.importance import importance_prompt

logger = logging.getLogger(__name__)


class ImportanceStrategy(ABC):
    @abstractmethod
    async def judge(self, db: AsyncSession, news: News) -> tuple[bool, str]:
        """Returns (is_important, reason)."""
        ...


class SampleBasedStrategy(ImportanceStrategy):
    """Strategy A: use category-specific examples for LLM judgment."""

    async def judge(self, db: AsyncSession, news: News) -> tuple[bool, str]:
        category = news.category or "其他"
        result = await db.execute(
            select(ImportanceExample).where(ImportanceExample.category == category)
        )
        examples = result.scalars().all()
        example_dicts = [
            {"title": e.title, "summary": e.summary, "is_important": e.is_important, "reason": e.reason}
            for e in examples
        ]

        messages = importance_prompt(
            news.title_zh or news.title,
            news.summary_zh or news.summary or "",
            category,
            example_dicts,
        )
        llm_result = await chat_completion(db, "importance", messages)

        lines = llm_result.strip().split("\n")
        is_important = "是" in lines[0] if lines else False
        reason = lines[1].replace("理由:", "").replace("理由：", "").strip() if len(lines) > 1 else ""
        return is_important, reason


# Default strategy
_strategy = SampleBasedStrategy()


def get_strategy() -> ImportanceStrategy:
    return _strategy


def set_strategy(strategy: ImportanceStrategy) -> None:
    global _strategy
    _strategy = strategy


async def judge_importance_for_news(db: AsyncSession, news: News) -> None:
    """Judge importance of a single news item."""
    strategy = get_strategy()
    try:
        is_important, reason = await strategy.judge(db, news)
        news.is_important = is_important
        news.importance_reason = reason
    except Exception as e:
        logger.error(f"Importance judgment failed for news {news.id}: {e}")
        news.is_important = None
        news.importance_reason = f"Error: {e}"


async def judge_importance_batch(db: AsyncSession) -> dict:
    """Judge importance for all similarity-checked news."""
    result = await db.execute(
        select(News).where(News.process_status == ProcessStatus.similarity_checked.value)
    )
    items = result.scalars().all()

    judged = 0
    important = 0
    for news in items:
        await judge_importance_for_news(db, news)
        news.process_status = ProcessStatus.completed.value
        judged += 1
        if news.is_important:
            important += 1

    await db.commit()
    return {"judged": judged, "important": important}
