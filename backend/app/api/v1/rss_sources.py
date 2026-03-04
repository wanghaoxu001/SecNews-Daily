import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.crud.rss_source import crud_rss_source
from app.database import async_session, get_db
from app.schemas.crawl_policy import CrawlPolicyResponse
from app.schemas.rss_source import RssSourceCreate, RssSourceUpdate, RssSourceResponse
from app.services.content_crawler import extract_domain_from_url
from app.services.crawl_policy_probe import (
    get_policy_response_by_domain,
    probe_domain_policy_for_source,
    probe_domain_policy_for_source_id,
)
from app.services.source_runner import run_source_pipeline

router = APIRouter(prefix="/rss-sources", tags=["rss-sources"], dependencies=[Depends(get_current_user)])


async def _to_source_response(db: AsyncSession, source) -> RssSourceResponse:
    domain = extract_domain_from_url(source.url)
    policy = await get_policy_response_by_domain(db, domain) if domain else None

    return RssSourceResponse(
        id=source.id,
        name=source.name,
        url=source.url,
        enabled=source.enabled,
        description=source.description,
        domain=domain or None,
        probe_status=(policy or {}).get("probe_status"),
        probe_last_run_at=(policy or {}).get("probe_last_run_at"),
        probe_last_error=(policy or {}).get("probe_last_error"),
        effective_wait_for_chain=(policy or {}).get("effective_wait_for_chain"),
        effective_timeouts_ms=(policy or {}).get("effective_timeouts_ms"),
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


@router.get("", response_model=list[RssSourceResponse])
async def list_sources(page: int = 1, page_size: int = 50, db: AsyncSession = Depends(get_db)):
    items, _ = await crud_rss_source.get_multi(db, offset=(page - 1) * page_size, limit=page_size)
    return [await _to_source_response(db, item) for item in items]


@router.get("/{source_id}", response_model=RssSourceResponse)
async def get_source(source_id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud_rss_source.get(db, source_id)
    if not obj:
        raise HTTPException(status_code=404, detail="RSS source not found")
    return await _to_source_response(db, obj)


@router.post("", response_model=RssSourceResponse, status_code=201)
async def create_source(body: RssSourceCreate, db: AsyncSession = Depends(get_db)):
    source = await crud_rss_source.create(db, obj_in=body)
    if settings.CRAWL_POLICY_PROBE_ENABLED and settings.CRAWL_POLICY_PROBE_TRIGGER_ON_CREATE:
        asyncio.create_task(probe_domain_policy_for_source_id(source.id))
    return await _to_source_response(db, source)


@router.put("/{source_id}", response_model=RssSourceResponse)
async def update_source(source_id: int, body: RssSourceUpdate, db: AsyncSession = Depends(get_db)):
    obj = await crud_rss_source.get(db, source_id)
    if not obj:
        raise HTTPException(status_code=404, detail="RSS source not found")
    updated = await crud_rss_source.update(db, db_obj=obj, obj_in=body)
    return await _to_source_response(db, updated)


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud_rss_source.delete(db, id=source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="RSS source not found")


@router.post("/{source_id}/probe-crawl-policy", response_model=CrawlPolicyResponse)
async def probe_source_crawl_policy(source_id: int, db: AsyncSession = Depends(get_db)):
    source = await crud_rss_source.get(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="RSS source not found")
    return await probe_domain_policy_for_source(db, source)


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
