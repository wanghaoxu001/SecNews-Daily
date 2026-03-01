import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.llm_client import chat_completion
from app.prompts.classify import classify_prompt, CATEGORIES

logger = logging.getLogger(__name__)


async def classify_news(db: AsyncSession, title: str, summary: str) -> str:
    """Classify news into one of 5 categories. Returns category string."""
    messages = classify_prompt(title, summary)
    result = await chat_completion(db, "classify", messages)
    result = result.strip()
    # Validate result is one of the known categories
    for cat in CATEGORIES:
        if cat in result:
            return cat
    logger.warning(f"Unknown classification result: {result}, defaulting to 其他")
    return "其他"
