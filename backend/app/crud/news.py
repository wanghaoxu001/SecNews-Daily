from datetime import datetime

from sqlalchemy import select, func, and_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import News


async def get_news(db: AsyncSession, news_id: int) -> News | None:
    return await db.get(News, news_id)


async def get_news_list(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    category: str | None = None,
    source_id: int | None = None,
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    is_similar: bool | None = None,
    is_important: bool | None = None,
) -> tuple[list[News], int]:
    conditions = []
    if status:
        conditions.append(News.process_status == status)
    if category:
        conditions.append(News.category == category)
    if source_id:
        conditions.append(News.source_id == source_id)
    if keyword:
        like_pattern = f"%{keyword}%"
        conditions.append(
            (News.title.ilike(like_pattern)) | (News.title_zh.ilike(like_pattern))
        )
    if date_from:
        conditions.append(News.published_at >= date_from)
    if date_to:
        conditions.append(News.published_at <= date_to)
    if is_similar is not None:
        conditions.append(News.is_similar == is_similar)
    if is_important is not None:
        conditions.append(News.is_important == is_important)

    where = and_(*conditions) if conditions else True

    total_q = await db.execute(select(func.count()).select_from(News).where(where))
    total = total_q.scalar_one()

    result = await db.execute(
        select(News)
        .where(where)
        .order_by(News.published_at.desc().nullslast(), News.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(result.scalars().all())
    return items, total


async def batch_reset_news_status(
    db: AsyncSession, news_ids: list[int], target_status: str
) -> int:
    """Reset news to target_status and clear downstream fields."""
    if not news_ids:
        return 0

    clear_fields: dict = {}

    if target_status == "pending":
        clear_fields = {
            News.title_zh: None,
            News.summary_zh: None,
            News.category: None,
            News.process_error: None,
            News.is_similar: False,
            News.similar_to_id: None,
            News.similarity_details: None,
            News.is_important: None,
            News.importance_reason: None,
            News.process_status: "pending",
        }
    elif target_status == "processed":
        clear_fields = {
            News.is_similar: False,
            News.similar_to_id: None,
            News.similarity_details: None,
            News.is_important: None,
            News.importance_reason: None,
            News.process_status: "processed",
        }
    elif target_status == "similarity_checked":
        clear_fields = {
            News.is_important: None,
            News.importance_reason: None,
            News.process_status: "similarity_checked",
        }
    else:
        return 0

    stmt = (
        update(News)
        .where(News.id.in_(news_ids))
        .values(**{c.key: v for c, v in clear_fields.items()})
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount  # type: ignore[return-value]


async def batch_delete_news(db: AsyncSession, news_ids: list[int]) -> int:
    """Delete news by IDs."""
    if not news_ids:
        return 0
    stmt = delete(News).where(News.id.in_(news_ids))
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount  # type: ignore[return-value]
