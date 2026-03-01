from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.crud.news import get_news, get_news_list
from app.schemas.news import NewsResponse, NewsListResponse

router = APIRouter(prefix="/news", tags=["news"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=NewsListResponse)
async def list_news(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    category: str | None = None,
    source_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    items, total = await get_news_list(
        db, page=page, page_size=page_size, status=status, category=category, source_id=source_id
    )
    return NewsListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{news_id}", response_model=NewsResponse)
async def get_news_detail(news_id: int, db: AsyncSession = Depends(get_db)):
    news = await get_news(db, news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news
