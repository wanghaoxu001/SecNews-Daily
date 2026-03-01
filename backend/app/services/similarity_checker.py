import logging

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


async def check_similarity_for_news(db: AsyncSession, news: News, days: int = 7) -> None:
    """Check if news is similar to recently published briefing news."""
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(days=days)

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
            llm_result = await chat_completion(db, "similarity", messages)
            if "是" in llm_result.split("\n")[0]:
                news.is_similar = True
                news.similar_to_id = candidate.id
                news.similarity_details = details
                return
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
