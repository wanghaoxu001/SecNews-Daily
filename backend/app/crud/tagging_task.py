from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.importance_example import ImportanceExample
from app.models.tagging_task import TaggingTask, TaggingTaskItem
from app.schemas.importance_example import ImportanceExampleCreate


def serialize_task(task: TaggingTask) -> dict:
    labeled_count = sum(1 for item in task.items if item.is_important is not None)
    return {
        "id": task.id,
        "original_file_name": task.original_file_name,
        "status": task.status,
        "total_count": task.total_count,
        "current_index": task.current_index,
        "labeled_count": labeled_count,
        "imported_at": task.imported_at,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


class CRUDTaggingTask:
    async def create_from_rows(
        self,
        db: AsyncSession,
        *,
        original_file_name: str,
        rows: list[dict[str, str]],
    ) -> TaggingTask:
        task = TaggingTask(
            original_file_name=original_file_name,
            status="in_progress",
            total_count=len(rows),
            current_index=0,
        )
        task.items = [
            TaggingTaskItem(
                row_index=index,
                title=row["title"],
                summary=row.get("summary") or None,
                category=row["category"],
                reason=row.get("reason") or None,
                raw_payload=row,
            )
            for index, row in enumerate(rows)
        ]
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return await self.get(db, task.id)  # type: ignore[return-value]

    async def get(self, db: AsyncSession, task_id: int) -> TaggingTask | None:
        result = await db.execute(
            select(TaggingTask).where(TaggingTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def list_tasks(self, db: AsyncSession) -> list[TaggingTask]:
        result = await db.execute(select(TaggingTask).order_by(TaggingTask.id.desc()))
        return list(result.scalars().all())

    async def update_cursor(self, db: AsyncSession, task: TaggingTask, current_index: int) -> TaggingTask:
        task.current_index = min(max(current_index, 0), task.total_count - 1)
        await db.commit()
        await db.refresh(task)
        return await self.get(db, task.id)  # type: ignore[return-value]

    async def get_item(self, db: AsyncSession, task_id: int, item_id: int) -> TaggingTaskItem | None:
        result = await db.execute(
            select(TaggingTaskItem).where(
                TaggingTaskItem.task_id == task_id,
                TaggingTaskItem.id == item_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_item(
        self,
        db: AsyncSession,
        *,
        task: TaggingTask,
        item: TaggingTaskItem,
        is_important: bool | None,
    ) -> tuple[TaggingTask, TaggingTaskItem]:
        item.is_important = is_important
        if task.status == "draft":
            task.status = "in_progress"
        await db.commit()
        await db.refresh(item)
        refreshed_task = await self.get(db, task.id)
        assert refreshed_task is not None
        return refreshed_task, item

    async def complete(self, db: AsyncSession, task: TaggingTask) -> TaggingTask:
        task.status = "completed"
        await db.commit()
        await db.refresh(task)
        return await self.get(db, task.id)  # type: ignore[return-value]

    async def import_examples(self, db: AsyncSession, task: TaggingTask) -> tuple[TaggingTask, int, int]:
        imported_count = 0
        skipped_count = 0

        for item in task.items:
            assert item.is_important is not None
            existing = await db.execute(
                select(ImportanceExample.id).where(
                    ImportanceExample.title == item.title,
                    ImportanceExample.category == item.category,
                    ImportanceExample.is_important == item.is_important,
                )
            )
            if existing.scalar_one_or_none() is not None:
                skipped_count += 1
                continue

            db.add(
                ImportanceExample(
                    **ImportanceExampleCreate(
                        title=item.title,
                        summary=item.summary,
                        category=item.category,
                        is_important=item.is_important,
                        reason=item.reason,
                    ).model_dump()
                )
            )
            imported_count += 1

        task.status = "imported"
        task.imported_at = datetime.utcnow().isoformat()
        await db.commit()
        await db.refresh(task)
        refreshed_task = await self.get(db, task.id)
        assert refreshed_task is not None
        return refreshed_task, imported_count, skipped_count


crud_tagging_task = CRUDTaggingTask()
