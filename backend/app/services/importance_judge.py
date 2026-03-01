import logging
import json
import re
from abc import ABC, abstractmethod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import News
from app.models.enums import ProcessStatus
from app.models.importance_example import ImportanceExample
from app.services.llm_client import chat_completion
from app.prompts.importance import importance_prompt

logger = logging.getLogger(__name__)
MAX_PARSE_ATTEMPTS = 3


def _sanitize_json_response(raw: str) -> str:
    text = raw.replace("\ufeff", "").strip()

    code_fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    if code_fence:
        text = code_fence.group(1).strip()

    obj_start = text.find("{")
    obj_end = text.rfind("}")
    if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
        text = text[obj_start:obj_end + 1]

    # Remove trailing commas before object/array close tokens.
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return text


def _parse_bool_value(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "是", "重要"}:
            return True
        if normalized in {"false", "0", "no", "n", "否", "不重要"}:
            return False
    return None


def _parse_importance_json(raw: str) -> tuple[bool, str]:
    cleaned = _sanitize_json_response(raw)

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON response: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Importance response must be a JSON object")

    raw_is_important = (
        payload.get("is_important")
        if "is_important" in payload
        else payload.get("important", payload.get("isImportant", payload.get("重要")))
    )
    is_important = _parse_bool_value(raw_is_important)
    if is_important is None:
        raise ValueError("Missing/invalid 'is_important' field in JSON response")

    raw_reason = payload.get("reason", payload.get("理由", ""))
    if raw_reason is None:
        reason = ""
    elif isinstance(raw_reason, (str, int, float, bool)):
        reason = str(raw_reason).strip()
    else:
        raise ValueError("Invalid 'reason' field type in JSON response")

    return is_important, reason


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

        current_messages = messages
        last_error: ValueError | None = None

        for attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
            llm_result = await chat_completion(db, "importance", current_messages)
            try:
                return _parse_importance_json(llm_result)
            except ValueError as exc:
                last_error = exc
                logger.warning(
                    "Failed to parse importance JSON (attempt %s/%s): %s",
                    attempt,
                    MAX_PARSE_ATTEMPTS,
                    exc,
                )
                if attempt == MAX_PARSE_ATTEMPTS:
                    break

                current_messages = current_messages + [
                    {"role": "assistant", "content": llm_result},
                    {
                        "role": "user",
                        "content": (
                            "你的输出不是合法 JSON。请仅返回一个 JSON 对象，且不要输出任何额外文本："
                            '{"is_important": true/false, "reason": "简短说明"}'
                        ),
                    },
                ]

        if last_error is not None:
            raise ValueError(f"Importance JSON parse failed after retries: {last_error}")
        raise RuntimeError("Importance JSON parse failed with unknown error")


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
