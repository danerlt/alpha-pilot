"""HTTP 请求级 access log 中间件。"""
from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("middleware.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: D401
        start = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.exception(
                "%s %s — exception (%dms)",
                request.method,
                request.url.path,
                elapsed_ms,
            )
            raise
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "%s %s -> %d (%dms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
