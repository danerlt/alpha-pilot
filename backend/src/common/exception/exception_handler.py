"""全局 exception handler。"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from src.common.exception.errors import AppBaseException
from src.common.response.response_code import ErrorCode
from src.utils.request_id import current_request_id

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger("app.exception_handler")


def register_exception_handlers(app: "FastAPI") -> None:
    """注册全局 exception handler。"""

    @app.exception_handler(AppBaseException)
    async def app_exc_handler(request, exc: AppBaseException) -> JSONResponse:  # noqa: D401
        """业务异常：仅做 JSON 转换；日志由 AppBaseException._auto_log 在抛出点已记。"""
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "code": exc.code,
                "message": exc.message,
                "data": None,
                "request_id": current_request_id(),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "code": ErrorCode.VALIDATION_ERROR.code,
                "message": ErrorCode.VALIDATION_ERROR.msg,
                "detailMessage": str(exc.errors()[:5]),
                "data": None,
                "request_id": current_request_id(),
            },
        )

    @app.exception_handler(PydanticValidationError)
    async def pydantic_handler(request, exc: PydanticValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "code": ErrorCode.VALIDATION_ERROR.code,
                "message": ErrorCode.VALIDATION_ERROR.msg,
                "detailMessage": str(exc.errors()[:5]),
                "data": None,
                "request_id": current_request_id(),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request, exc: Exception) -> JSONResponse:
        """未识别异常：记 ERROR + 完整 traceback（这类没有 auto_log）。"""
        # 让 FastAPI 内置的 HTTPException / Starlette 的 HTTPException 走默认处理
        from fastapi import HTTPException as FastAPIHTTPException
        from starlette.exceptions import HTTPException as StarletteHTTPException

        if isinstance(exc, (FastAPIHTTPException, StarletteHTTPException)):
            raise exc

        logger.error(
            "[Unhandled] %s %s — %s",
            request.method,
            request.url.path,
            str(exc),
            exc_info=exc,
            extra={
                "request_id": current_request_id(),
                "method": request.method,
                "path": str(request.url.path),
            },
        )
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "code": ErrorCode.SYS_ERROR.code,
                "message": ErrorCode.SYS_ERROR.msg,
                "data": None,
                "request_id": current_request_id(),
            },
        )
