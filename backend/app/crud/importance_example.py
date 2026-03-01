from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.importance_example import ImportanceExample
from app.schemas.importance_example import ImportanceExampleCreate, ImportanceExampleUpdate


class CRUDImportanceExample(CRUDBase[ImportanceExample, ImportanceExampleCreate, ImportanceExampleUpdate]):
    async def get_by_category(self, db: AsyncSession, category: str) -> list[ImportanceExample]:
        result = await db.execute(
            select(ImportanceExample).where(ImportanceExample.category == category)
        )
        return list(result.scalars().all())

    async def bulk_create(self, db: AsyncSession, items: list[ImportanceExampleCreate]) -> list[ImportanceExample]:
        objs = [ImportanceExample(**item.model_dump()) for item in items]
        db.add_all(objs)
        await db.commit()
        for obj in objs:
            await db.refresh(obj)
        return objs


crud_importance_example = CRUDImportanceExample(ImportanceExample)
