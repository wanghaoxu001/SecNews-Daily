import logging
import json
import re
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.llm_client import chat_completion
from app.prompts.classify import classify_prompt, CATEGORIES

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

    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return text


def _parse_classification_json(raw: str) -> str:
    cleaned = _sanitize_json_response(raw)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON response: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Classification response must be a JSON object")

    raw_category = payload.get("category", payload.get("label", payload.get("分类")))
    if not isinstance(raw_category, str):
        raise ValueError("Missing/invalid 'category' field in JSON response")

    category = raw_category.strip()
    if category not in CATEGORIES:
        raise ValueError(f"Unknown category: {category}")
    return category


async def classify_news(db: AsyncSession, title: str, summary: str) -> str:
    """Classify news into one of 5 categories. Returns category string."""
    messages = classify_prompt(title, summary)
    current_messages = messages
    last_error: ValueError | None = None

    for attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
        result = await chat_completion(db, "classify", current_messages)
        try:
            return _parse_classification_json(result)
        except ValueError as exc:
            last_error = exc
            logger.warning(
                "Failed to parse classification JSON (attempt %s/%s): %s",
                attempt,
                MAX_PARSE_ATTEMPTS,
                exc,
            )
            if attempt == MAX_PARSE_ATTEMPTS:
                break

            current_messages = current_messages + [
                {"role": "assistant", "content": result},
                {
                    "role": "user",
                    "content": (
                        "你的输出不是合法 JSON。请仅返回一个 JSON 对象，且不要输出任何额外文本："
                        '{"category": "分类名称"}'
                    ),
                },
            ]

    if last_error is not None:
        logger.warning("Classification fallback to 其他 after retries: %s", last_error)
    return "其他"
