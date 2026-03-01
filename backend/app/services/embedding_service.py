import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.llm_client import get_embedding

logger = logging.getLogger(__name__)


async def generate_and_store_embedding(db: AsyncSession, news) -> None:
    """Generate embedding for news and store in the model."""
    text = f"{news.title_zh or news.title} {news.summary_zh or news.summary or ''}"
    try:
        embedding = await get_embedding(db, "embedding", text)
        news.embedding = embedding
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to generate embedding for news {news.id}: {e}")
