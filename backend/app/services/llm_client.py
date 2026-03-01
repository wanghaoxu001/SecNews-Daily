import asyncio
import logging
import time

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_config import LlmConfig
from app.models.processing_config import ProcessingConfig

logger = logging.getLogger(__name__)

# Global cooldown state — shared across all LLM calls
_cooldown_lock = asyncio.Lock()
_last_call_time: float = 0.0


async def _get_cooldown_seconds(db: AsyncSession) -> float:
    """Read llm_cooldown_seconds from ProcessingConfig, default 0."""
    result = await db.execute(
        select(ProcessingConfig.value).where(ProcessingConfig.key == "llm_cooldown_seconds")
    )
    val = result.scalar_one_or_none()
    if val is None:
        return 0.0
    try:
        return max(0.0, float(val))
    except (ValueError, TypeError):
        return 0.0


async def _wait_cooldown(db: AsyncSession) -> None:
    """Wait until the cooldown period since the last LLM call has elapsed."""
    global _last_call_time
    cooldown = await _get_cooldown_seconds(db)
    if cooldown <= 0:
        return
    async with _cooldown_lock:
        elapsed = time.monotonic() - _last_call_time
        if elapsed < cooldown:
            wait = cooldown - elapsed
            logger.debug(f"LLM cooldown: waiting {wait:.1f}s")
            await asyncio.sleep(wait)
        _last_call_time = time.monotonic()


def _mark_call_done() -> None:
    """Record the time when an LLM call finishes."""
    global _last_call_time
    _last_call_time = time.monotonic()


async def _get_config(db: AsyncSession, task_type: str) -> dict:
    """Load LLM config for task_type, falling back to default for missing fields."""
    result = await db.execute(select(LlmConfig).where(LlmConfig.task_type == task_type))
    cfg = result.scalar_one_or_none()
    default_result = await db.execute(select(LlmConfig).where(LlmConfig.task_type == "default"))
    default = default_result.scalar_one_or_none()

    if cfg is None and default is None:
        raise ValueError(f"No LLM config found for task_type={task_type} or default")

    base = default or cfg
    override = cfg if cfg and cfg != base else None

    return {
        "base_url": (override.base_url if override and override.base_url else None) or (base.base_url if base else None),
        "api_key": (override.api_key if override and override.api_key else None) or (base.api_key if base else None),
        "model": (override.model if override and override.model else None) or (base.model if base else None),
        "temperature": (override.temperature if override and override.temperature is not None else None)
        if override
        else (base.temperature if base else None),
        "max_tokens": (override.max_tokens if override and override.max_tokens is not None else None)
        if override
        else (base.max_tokens if base else None),
    }


async def chat_completion(
    db: AsyncSession, task_type: str, messages: list[dict], **kwargs
) -> str:
    """Call OpenAI-compatible chat completion API with retry."""
    config = await _get_config(db, task_type)

    headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"}
    payload = {
        "model": config["model"],
        "messages": messages,
    }
    if config["temperature"] is not None:
        payload["temperature"] = config["temperature"]
    if config["max_tokens"] is not None:
        payload["max_tokens"] = config["max_tokens"]
    payload.update(kwargs)

    url = f"{config['base_url'].rstrip('/')}/v1/chat/completions"

    await _wait_cooldown(db)
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                _mark_call_done()
                return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError) as e:
            logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                raise
            await asyncio.sleep(2 ** attempt)
    raise RuntimeError("LLM call failed after retries")


async def get_embedding(db: AsyncSession, task_type: str, text: str) -> list[float]:
    """Call OpenAI-compatible embeddings API."""
    config = await _get_config(db, task_type)

    headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"}
    payload = {"model": config["model"], "input": text}
    url = f"{config['base_url'].rstrip('/')}/v1/embeddings"

    await _wait_cooldown(db)
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        _mark_call_done()
        return data["data"][0]["embedding"]
