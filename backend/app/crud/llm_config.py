from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.enums import LlmTaskType
from app.models.llm_config import LlmConfig
from app.schemas.llm_config import LlmConfigCreate, LlmConfigUpdate

ALL_TASK_TYPES = [t.value for t in LlmTaskType]


class CRUDLlmConfig(CRUDBase[LlmConfig, LlmConfigCreate, LlmConfigUpdate]):
    async def get_by_task_type(self, db: AsyncSession, task_type: str) -> LlmConfig | None:
        result = await db.execute(select(LlmConfig).where(LlmConfig.task_type == task_type))
        return result.scalar_one_or_none()

    async def get_resolved(self, db: AsyncSession, task_type: str) -> dict | None:
        """Get config for task_type, inheriting missing fields from 'default'."""
        cfg = await self.get_by_task_type(db, task_type)
        if cfg is None:
            return None
        default = await self.get_by_task_type(db, "default") if task_type != "default" else None
        result = {
            "id": cfg.id,
            "task_type": cfg.task_type,
            "base_url": cfg.base_url or (default.base_url if default else None),
            "api_key": cfg.api_key or (default.api_key if default else None),
            "model": cfg.model or (default.model if default else None),
            "temperature": cfg.temperature if cfg.temperature is not None else (default.temperature if default else None),
            "max_tokens": cfg.max_tokens if cfg.max_tokens is not None else (default.max_tokens if default else None),
            "created_at": cfg.created_at,
            "updated_at": cfg.updated_at,
        }
        return result

    async def ensure_all_task_types(self, db: AsyncSession) -> list[LlmConfig]:
        """Ensure a row exists for every LlmTaskType. Returns all configs."""
        result = await db.execute(select(LlmConfig))
        existing = {cfg.task_type for cfg in result.scalars().all()}
        for tt in ALL_TASK_TYPES:
            if tt not in existing:
                db.add(LlmConfig(task_type=tt))
        await db.commit()
        result = await db.execute(select(LlmConfig).order_by(LlmConfig.id))
        return list(result.scalars().all())


crud_llm_config = CRUDLlmConfig(LlmConfig)
