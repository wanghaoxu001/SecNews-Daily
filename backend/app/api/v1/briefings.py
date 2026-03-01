from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.crud.briefing import (
    get_briefing, get_briefings, create_briefing_from_news,
    update_briefing, delete_briefing, get_latest_briefing,
)
from app.schemas.briefing import (
    BriefingCreate, BriefingUpdate, BriefingResponse, BriefingListResponse,
)

router = APIRouter(prefix="/briefings", tags=["briefings"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[BriefingListResponse])
async def list_briefings(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, _ = await get_briefings(db, page=page, page_size=page_size)
    result = []
    for b in items:
        result.append(BriefingListResponse(
            id=b.id, title=b.title, date=b.date, status=b.status,
            item_count=len(b.items), created_at=b.created_at,
        ))
    return result


@router.get("/latest")
async def get_latest(db: AsyncSession = Depends(get_db)):
    briefing = await get_latest_briefing(db)
    if not briefing:
        return None
    return BriefingResponse.model_validate(briefing)


@router.get("/{briefing_id}", response_model=BriefingResponse)
async def get_briefing_detail(briefing_id: int, db: AsyncSession = Depends(get_db)):
    briefing = await get_briefing(db, briefing_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")
    return briefing


@router.post("", response_model=BriefingResponse, status_code=201)
async def create_briefing(body: BriefingCreate, db: AsyncSession = Depends(get_db)):
    return await create_briefing_from_news(db, body.title, body.date, body.news_ids)


@router.put("/{briefing_id}", response_model=BriefingResponse)
async def update_briefing_route(
    briefing_id: int, body: BriefingUpdate, db: AsyncSession = Depends(get_db),
):
    briefing = await get_briefing(db, briefing_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")
    return await update_briefing(db, briefing, **body.model_dump(exclude_unset=True))


@router.delete("/{briefing_id}", status_code=204)
async def delete_briefing_route(briefing_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await delete_briefing(db, briefing_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Briefing not found")
