"""未捕获异常兜底 middleware。

注意：FastAPI 的全局 exception handler 已经覆盖大多数情况；本 middleware 是
最后一道防线，确保异常一定会被记日志，避免在 starlette 层吃掉。
"""
from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("middleware.error")


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: D401
        try:
            return await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled in middleware-stack: %s %s",
                request.method,
                request.url.path,
            )
            raise
