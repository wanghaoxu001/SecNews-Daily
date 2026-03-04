from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.schemas.crawl_policy import CrawlPolicyResponse
from app.services.crawl_policy_probe import get_policy_response_by_domain

router = APIRouter(prefix="/crawl-policies", tags=["crawl-policies"], dependencies=[Depends(get_current_user)])


@router.get("/{domain}", response_model=CrawlPolicyResponse)
async def get_crawl_policy(domain: str, db: AsyncSession = Depends(get_db)):
    payload = await get_policy_response_by_domain(db, domain)
    if payload is None:
        raise HTTPException(status_code=404, detail="Crawl policy not found")
    return payload
