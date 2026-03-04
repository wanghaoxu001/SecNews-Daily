from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.core.logging import RequestLoggingMiddleware, setup_logging
from app.services.scheduler import start_scheduler, stop_scheduler

setup_logging(
    settings.LOG_LEVEL,
    log_to_file=settings.LOG_TO_FILE,
    log_file_path=settings.LOG_FILE_PATH,
    log_file_max_bytes=settings.LOG_FILE_MAX_BYTES,
    log_file_backup_count=settings.LOG_FILE_BACKUP_COUNT,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_scheduler()
    yield
    stop_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(title="SecNews-Daily", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health_check():
        return {"status": "ok"}

    app.add_middleware(RequestLoggingMiddleware)

    app.include_router(api_router)

    return app


app = create_app()
