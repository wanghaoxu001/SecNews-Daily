from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.briefing import Briefing, BriefingItem
from app.models.news import News


async def get_briefing(db: AsyncSession, briefing_id: int) -> Briefing | None:
    return await db.get(Briefing, briefing_id)


async def get_briefings(db: AsyncSession, page: int = 1, page_size: int = 20) -> tuple[list[Briefing], int]:
    total_q = await db.execute(select(func.count()).select_from(Briefing))
    total = total_q.scalar_one()
    result = await db.execute(
        select(Briefing).order_by(Briefing.date.desc(), Briefing.id.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    return list(result.scalars().all()), total


async def create_briefing_from_news(
    db: AsyncSession, title: str, date, news_ids: list[int]
) -> Briefing:
    briefing = Briefing(title=title, date=date, status="draft")
    db.add(briefing)
    await db.flush()

    sort_order = 0
    for news_id in news_ids:
        news = await db.get(News, news_id)
        if news:
            item = BriefingItem(
                briefing_id=briefing.id,
                news_id=news.id,
                title=news.title_zh or news.title,
                summary=news.summary_zh or news.summary or "",
                category=news.category,
                sort_order=sort_order,
            )
            db.add(item)
            sort_order += 1

    await db.commit()
    await db.refresh(briefing)
    return briefing


async def update_briefing(db: AsyncSession, briefing: Briefing, **kwargs) -> Briefing:
    for k, v in kwargs.items():
        if v is not None:
            setattr(briefing, k, v)
    await db.commit()
    await db.refresh(briefing)
    return briefing


async def delete_briefing(db: AsyncSession, briefing_id: int) -> bool:
    briefing = await db.get(Briefing, briefing_id)
    if not briefing:
        return False
    await db.delete(briefing)
    await db.commit()
    return True


async def get_briefing_item(db: AsyncSession, item_id: int) -> BriefingItem | None:
    return await db.get(BriefingItem, item_id)


async def update_briefing_item(db: AsyncSession, item: BriefingItem, **kwargs) -> BriefingItem:
    for k, v in kwargs.items():
        if v is not None:
            setattr(item, k, v)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_briefing_item(db: AsyncSession, item_id: int) -> bool:
    item = await db.get(BriefingItem, item_id)
    if not item:
        return False
    await db.delete(item)
    await db.commit()
    return True


async def reorder_briefing_items(db: AsyncSession, briefing_id: int, item_ids: list[int]) -> None:
    for idx, item_id in enumerate(item_ids):
        item = await db.get(BriefingItem, item_id)
        if item and item.briefing_id == briefing_id:
            item.sort_order = idx
    await db.commit()


async def get_latest_briefing(db: AsyncSession) -> Briefing | None:
    result = await db.execute(
        select(Briefing).order_by(Briefing.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()
