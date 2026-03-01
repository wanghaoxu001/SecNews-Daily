from typing import TypeVar, Generic, Type, Sequence

from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> ModelType | None:
        return await db.get(self.model, id)

    async def get_multi(
        self, db: AsyncSession, *, offset: int = 0, limit: int = 20
    ) -> tuple[Sequence[ModelType], int]:
        total_result = await db.execute(select(func.count()).select_from(self.model))
        total = total_result.scalar_one()
        result = await db.execute(
            select(self.model).offset(offset).limit(limit).order_by(self.model.id.desc())
        )
        items = result.scalars().all()
        return items, total

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj = self.model(**obj_in.model_dump())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update(self, db: AsyncSession, *, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: int) -> bool:
        obj = await db.get(self.model, id)
        if obj is None:
            return False
        await db.delete(obj)
        await db.commit()
        return True
