import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.crud.news import get_news, get_news_list, batch_reset_news_status, batch_delete_news
from app.schemas.news import (
    NewsResponse,
    NewsListResponse,
    BatchReprocessRequest,
    BatchReprocessResponse,
    BatchDeleteRequest,
    BatchDeleteResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["news"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=NewsListResponse)
async def list_news(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    category: str | None = None,
    source_id: int | None = None,
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    is_similar: bool | None = None,
    is_important: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    items, total = await get_news_list(
        db,
        page=page,
        page_size=page_size,
        status=status,
        category=category,
        source_id=source_id,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
        is_similar=is_similar,
        is_important=is_important,
    )
    return NewsListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/batch-reprocess", response_model=BatchReprocessResponse)
async def batch_reprocess_news(
    body: BatchReprocessRequest,
    db: AsyncSession = Depends(get_db),
):
    reset_count = await batch_reset_news_status(db, body.news_ids, body.target_status)
    if reset_count == 0:
        raise HTTPException(status_code=404, detail="No news matched the given IDs")

    pipeline_result: dict = {}
    try:
        if body.target_status == "pending":
            from app.services.news_processor import process_pending_news
            from app.services.similarity_checker import check_similarity_batch
            from app.services.importance_judge import judge_importance_batch

            pipeline_result["process"] = await process_pending_news(db)
            pipeline_result["similarity"] = await check_similarity_batch(db)
            pipeline_result["importance"] = await judge_importance_batch(db)

        elif body.target_status == "processed":
            from app.services.similarity_checker import check_similarity_batch
            from app.services.importance_judge import judge_importance_batch

            pipeline_result["similarity"] = await check_similarity_batch(db)
            pipeline_result["importance"] = await judge_importance_batch(db)

        elif body.target_status == "similarity_checked":
            from app.services.importance_judge import judge_importance_batch

            pipeline_result["importance"] = await judge_importance_batch(db)

    except Exception as e:
        logger.exception("Pipeline error during batch reprocess")
        pipeline_result["error"] = str(e)

    return BatchReprocessResponse(reset_count=reset_count, pipeline_result=pipeline_result)


@router.post("/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_news_endpoint(
    body: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    deleted_count = await batch_delete_news(db, body.news_ids)
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="No news matched the given IDs")
    return BatchDeleteResponse(deleted_count=deleted_count)


@router.get("/{news_id}", response_model=NewsResponse)
async def get_news_detail(news_id: int, db: AsyncSession = Depends(get_db)):
    news = await get_news(db, news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news
