from sqlalchemy import select, func, and_
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
) -> tuple[list[News], int]:
    conditions = []
    if status:
        conditions.append(News.process_status == status)
    if category:
        conditions.append(News.category == category)
    if source_id:
        conditions.append(News.source_id == source_id)

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
