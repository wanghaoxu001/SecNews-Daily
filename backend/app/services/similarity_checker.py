import logging
import json
import re

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import News
from app.models.enums import ProcessStatus
from app.services.entity_extractor import extract_entities, entity_overlap_score
from app.services.keyword_analyzer import tfidf_cosine_similarity
from app.services.llm_client import chat_completion
from app.prompts.similarity import similarity_prompt

logger = logging.getLogger(__name__)

# Weights for the three similarity signals
ENTITY_WEIGHT = 0.3
KEYWORD_WEIGHT = 0.4
EMBEDDING_WEIGHT = 0.3
SIMILARITY_THRESHOLD = 0.5
TOP_K = 3
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


def _parse_bool_value(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "是", "相似"}:
            return True
        if normalized in {"false", "0", "no", "n", "否", "不相似"}:
            return False
    return None


def _parse_similarity_json(raw: str) -> tuple[bool, str]:
    cleaned = _sanitize_json_response(raw)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON response: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Similarity response must be a JSON object")

    raw_is_similar = (
        payload.get("is_similar")
        if "is_similar" in payload
        else payload.get("similar", payload.get("isSimilar", payload.get("相似")))
    )
    is_similar = _parse_bool_value(raw_is_similar)
    if is_similar is None:
        raise ValueError("Missing/invalid 'is_similar' field in JSON response")

    raw_reason = payload.get("reason", payload.get("理由", ""))
    if raw_reason is None:
        reason = ""
    elif isinstance(raw_reason, (str, int, float, bool)):
        reason = str(raw_reason).strip()
    else:
        raise ValueError("Invalid 'reason' field type in JSON response")

    return is_similar, reason


async def check_similarity_for_news(db: AsyncSession, news: News, days: int = 7) -> None:
    """Check if news is similar to recently published briefing news."""
    from datetime import timedelta
    from app.core.timezone import now_utc

    cutoff = now_utc() - timedelta(days=days)

    # Get candidate pool: recent completed news in same category
    result = await db.execute(
        select(News).where(
            and_(
                News.id != news.id,
                News.category == news.category,
                News.process_status == ProcessStatus.completed.value,
                News.created_at >= cutoff,
            )
        )
    )
    candidates = result.scalars().all()

    if not candidates:
        news.is_similar = False
        return

    news_text = f"{news.title_zh or news.title} {news.summary_zh or news.summary or ''}"
    news_entities = extract_entities(news_text)

    scored = []
    for candidate in candidates:
        cand_text = f"{candidate.title_zh or candidate.title} {candidate.summary_zh or candidate.summary or ''}"
        cand_entities = extract_entities(cand_text)

        entity_score = entity_overlap_score(news_entities, cand_entities)
        keyword_score = tfidf_cosine_similarity(news_text, cand_text)

        # Embedding cosine similarity (if both have embeddings)
        embedding_score = 0.0
        if news.embedding is not None and candidate.embedding is not None:
            # pgvector cosine distance
            dot = sum(a * b for a, b in zip(news.embedding, candidate.embedding))
            norm_a = sum(a ** 2 for a in news.embedding) ** 0.5
            norm_b = sum(b ** 2 for b in candidate.embedding) ** 0.5
            if norm_a > 0 and norm_b > 0:
                embedding_score = dot / (norm_a * norm_b)

        weighted = (
            entity_score * ENTITY_WEIGHT
            + keyword_score * KEYWORD_WEIGHT
            + embedding_score * EMBEDDING_WEIGHT
        )
        scored.append((candidate, weighted, {
            "entity": entity_score,
            "keyword": keyword_score,
            "embedding": embedding_score,
            "weighted": weighted,
        }))

    scored.sort(key=lambda x: x[1], reverse=True)
    top_candidates = scored[:TOP_K]

    # Send top candidates to LLM for final judgment
    for candidate, score, details in top_candidates:
        if score < SIMILARITY_THRESHOLD:
            continue
        try:
            messages = similarity_prompt(
                news.title_zh or news.title,
                news.summary_zh or news.summary or "",
                candidate.title_zh or candidate.title,
                candidate.summary_zh or candidate.summary or "",
            )
            current_messages = messages

            for attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
                llm_result = await chat_completion(db, "similarity", current_messages)
                try:
                    is_similar, reason = _parse_similarity_json(llm_result)
                    if is_similar:
                        news.is_similar = True
                        news.similar_to_id = candidate.id
                        news.similarity_details = {**details, "llm_reason": reason}
                        return
                    break
                except ValueError as exc:
                    logger.warning(
                        "Failed to parse similarity JSON (attempt %s/%s): %s",
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
                                '{"is_similar": true/false, "reason": "简短说明"}'
                            ),
                        },
                    ]
        except Exception as e:
            logger.warning(f"LLM similarity check failed: {e}")

    news.is_similar = False


async def check_similarity_batch(db: AsyncSession) -> dict:
    """Check similarity for all processed news."""
    result = await db.execute(
        select(News).where(News.process_status == ProcessStatus.processed.value)
    )
    items = result.scalars().all()

    checked = 0
    similar = 0
    for news in items:
        await check_similarity_for_news(db, news)
        news.process_status = ProcessStatus.similarity_checked.value
        checked += 1
        if news.is_similar:
            similar += 1

    await db.commit()
    return {"checked": checked, "similar": similar}
