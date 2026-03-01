from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.crud.briefing import (
    get_briefing_item, update_briefing_item, delete_briefing_item, reorder_briefing_items,
)
from app.schemas.briefing import BriefingItemUpdate, BriefingItemResponse

router = APIRouter(prefix="/briefing-items", tags=["briefing-items"], dependencies=[Depends(get_current_user)])


@router.put("/{item_id}", response_model=BriefingItemResponse)
async def update_item(
    item_id: int, body: BriefingItemUpdate, db: AsyncSession = Depends(get_db),
):
    item = await get_briefing_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Briefing item not found")
    return await update_briefing_item(db, item, **body.model_dump(exclude_unset=True))


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await delete_briefing_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Briefing item not found")


class ReorderRequest(BaseModel):
    item_ids: list[int]


@router.post("/reorder/{briefing_id}", status_code=200)
async def reorder_items(
    briefing_id: int, body: ReorderRequest, db: AsyncSession = Depends(get_db),
):
    await reorder_briefing_items(db, briefing_id, body.item_ids)
    return {"status": "ok"}
