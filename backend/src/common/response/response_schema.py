"""统一响应 schema。"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from src.common.response.response_code import ErrorCode

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """HTTP API 统一响应 envelope。

    - 业务异常统一 HTTP 200 + body ``success: false``
    - HTTP 状态码留给传输层语义（404 路径不存在 / 401 未授权 等）
    """

    model_config = ConfigDict(populate_by_name=True)

    success: bool = Field(default=True)
    code: str = Field(default=ErrorCode.SUCCESS.code)
    message: str = Field(default=ErrorCode.SUCCESS.msg)
    detail_message: str | None = Field(default=None, alias="detailMessage")
    data: T | None = Field(default=None)
    request_id: str | None = Field(default=None)


class ResponseBase:
    """便捷构造器。"""

    @staticmethod
    def success(data: Any = None) -> Response:
        from src.utils.request_id import get_request_id

        return Response(
            success=True,
            code=ErrorCode.SUCCESS.code,
            message=ErrorCode.SUCCESS.msg,
            data=data,
            request_id=get_request_id(),
        )

    @staticmethod
    def fail(code: str, message: str, detail: str | None = None) -> Response:
        from src.utils.request_id import get_request_id

        return Response(
            success=False,
            code=code,
            message=message,
            detail_message=detail,
            data=None,
            request_id=get_request_id(),
        )


response_base = ResponseBase()
