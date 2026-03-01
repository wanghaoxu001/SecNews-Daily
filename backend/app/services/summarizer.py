import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.llm_client import chat_completion
from app.prompts.summarize import summarize_prompt

logger = logging.getLogger(__name__)


async def generate_summary(db: AsyncSession, content: str) -> str:
    """Generate Chinese summary from article content."""
    messages = summarize_prompt(content)
    return await chat_completion(db, "summarize", messages)
