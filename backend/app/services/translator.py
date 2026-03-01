import logging
from langdetect import detect

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.llm_client import chat_completion
from app.prompts.translate import translate_prompt

logger = logging.getLogger(__name__)


def is_chinese(text: str) -> bool:
    try:
        return detect(text) == "zh-cn" or detect(text) == "zh-tw"
    except Exception:
        return False


async def translate_text(db: AsyncSession, text: str) -> str:
    """Translate text to Chinese. Returns original if already Chinese."""
    if not text or is_chinese(text):
        return text
    messages = translate_prompt(text)
    return await chat_completion(db, "translate", messages)
