from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.rss_sources import router as rss_sources_router
from app.api.v1.llm_configs import router as llm_configs_router
from app.api.v1.task_configs import router as task_configs_router
from app.api.v1.processing_configs import router as processing_configs_router
from app.api.v1.importance_examples import router as importance_examples_router
from app.api.v1.crawl_policies import router as crawl_policies_router
from app.api.v1.news import router as news_router
from app.api.v1.pipeline import router as pipeline_router
from app.api.v1.briefings import router as briefings_router
from app.api.v1.briefing_items import router as briefing_items_router
from app.api.v1.tagging_tasks import router as tagging_tasks_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(rss_sources_router)
api_router.include_router(llm_configs_router)
api_router.include_router(task_configs_router)
api_router.include_router(processing_configs_router)
api_router.include_router(importance_examples_router)
api_router.include_router(crawl_policies_router)
api_router.include_router(news_router)
api_router.include_router(pipeline_router)
api_router.include_router(briefings_router)
api_router.include_router(briefing_items_router)
api_router.include_router(tagging_tasks_router)
