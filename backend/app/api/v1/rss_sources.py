import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.auth import get_current_user
from app.crud.rss_source import crud_rss_source
from app.schemas.rss_source import RssSourceCreate, RssSourceUpdate, RssSourceResponse
from app.services.source_runner import run_source_pipeline

router = APIRouter(prefix="/rss-sources", tags=["rss-sources"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[RssSourceResponse])
async def list_sources(page: int = 1, page_size: int = 50, db: AsyncSession = Depends(get_db)):
    items, _ = await crud_rss_source.get_multi(db, offset=(page - 1) * page_size, limit=page_size)
    return items


@router.get("/{source_id}", response_model=RssSourceResponse)
async def get_source(source_id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud_rss_source.get(db, source_id)
    if not obj:
        raise HTTPException(status_code=404, detail="RSS source not found")
    return obj


@router.post("", response_model=RssSourceResponse, status_code=201)
async def create_source(body: RssSourceCreate, db: AsyncSession = Depends(get_db)):
    return await crud_rss_source.create(db, obj_in=body)


@router.put("/{source_id}", response_model=RssSourceResponse)
async def update_source(source_id: int, body: RssSourceUpdate, db: AsyncSession = Depends(get_db)):
    obj = await crud_rss_source.get(db, source_id)
    if not obj:
        raise HTTPException(status_code=404, detail="RSS source not found")
    return await crud_rss_source.update(db, db_obj=obj, obj_in=body)


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud_rss_source.delete(db, id=source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="RSS source not found")


@router.post("/{source_id}/run")
async def run_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    """Run the full pipeline for a single RSS source, streaming progress via SSE."""
    source = await crud_rss_source.get(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="RSS source not found")

    # Capture source data before Depends session closes
    source_id_val = source.id
    source_name = source.name
    source_url = source.url
    source_enabled = source.enabled

    async def generate():
        # Use a self-managed session since StreamingResponse runs after endpoint returns
        async with async_session() as stream_db:
            from app.models.rss_source import RssSource as RssSourceModel
            src = await stream_db.get(RssSourceModel, source_id_val)
            if not src:
                evt = {"step": "done", "status": "error", "message": "RSS 源不存在"}
                yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"
                return
            async for event in run_source_pipeline(stream_db, src):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
