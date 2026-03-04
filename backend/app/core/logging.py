import logging
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


def setup_logging(
    level: str = "INFO",
    log_to_file: bool = False,
    log_file_path: str = "logs/backend.log",
    log_file_max_bytes: int = 10485760,
    log_file_backup_count: int = 7,
) -> None:
    """Configure root logger with stdout and optional rotating file output."""
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level.upper())

    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    root.addHandler(stdout_handler)

    if log_to_file:
        try:
            log_path = Path(log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max(1, log_file_max_bytes),
                backupCount=max(1, log_file_backup_count),
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except OSError as exc:
            root.warning("Failed to initialize file logging at %s: %s", log_file_path, exc)

    for name in ("httpx", "httpcore", "apscheduler", "uvicorn.access"):
        logging.getLogger(name).setLevel(logging.WARNING)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log method, path, status code, and duration for each request."""

    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("app.middleware.request")

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path == "/api/health":
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        self.logger.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
