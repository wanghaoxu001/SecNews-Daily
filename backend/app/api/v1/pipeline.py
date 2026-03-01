from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.services.rss_fetcher import fetch_all_sources
from app.services.news_processor import process_pending_news
from app.services.similarity_checker import check_similarity_batch
from app.services.importance_judge import judge_importance_batch
from app.services.pipeline_orchestrator import run_full_pipeline

router = APIRouter(prefix="/pipeline", tags=["pipeline"], dependencies=[Depends(get_current_user)])


@router.post("/fetch-rss")
async def trigger_fetch_rss(db: AsyncSession = Depends(get_db)):
    return await fetch_all_sources(db)


@router.post("/process-news")
async def trigger_process_news(db: AsyncSession = Depends(get_db)):
    return await process_pending_news(db)


@router.post("/check-similarity")
async def trigger_check_similarity(db: AsyncSession = Depends(get_db)):
    return await check_similarity_batch(db)


@router.post("/judge-importance")
async def trigger_judge_importance(db: AsyncSession = Depends(get_db)):
    return await judge_importance_batch(db)


@router.post("/run-full")
async def trigger_full_pipeline(db: AsyncSession = Depends(get_db)):
    return await run_full_pipeline(db)
