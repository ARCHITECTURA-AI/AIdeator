"""Logging setup for container-friendly stdout/stderr emission.

Grep tips:
- run lifecycle: `event=run_created|run_started|run_succeeded|run_failed`
- request traces: `event=request_completed`
- failures: `level=ERROR` with `exc_info`
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from api.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        event = getattr(record, "event", None)
        if event:
            payload["event"] = event
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class TextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now(timezone.utc).isoformat()
        event = getattr(record, "event", "")
        extra = getattr(record, "extra_fields", {})
        extra_blob = ""
        if isinstance(extra, dict) and extra:
            extra_blob = " " + " ".join(f"{k}={v}" for k, v in extra.items())
        base = (
            f"{ts} level={record.levelname} logger={record.name}"
            f" event={event} msg={record.getMessage()}{extra_blob}"
        )
        if record.exc_info:
            return f"{base}\n{self.formatException(record.exc_info)}"
        return base


def setup_logging() -> None:
    level_name = settings.log_level.upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if settings.log_json else TextFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)


def _safe_path(path: str) -> str:
    return path if path else "/"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        logger = logging.getLogger("api.request")
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "Request failed",
                extra={
                    "event": "request_failed",
                    "extra_fields": {
                        "method": request.method,
                        "path": _safe_path(request.url.path),
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                    },
                },
                exc_info=True,
            )
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            if status_code < 500:
                logger.info(
                    "Request completed",
                    extra={
                        "event": "request_completed",
                        "extra_fields": {
                            "method": request.method,
                            "path": _safe_path(request.url.path),
                            "status_code": status_code,
                            "duration_ms": duration_ms,
                        },
                    },
                )
