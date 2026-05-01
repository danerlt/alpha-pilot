"""@api_response 装饰器：自动包装 router 返回值为 Response[T]。

stage 4 wave 2 应用到所有 controllers/api/v1/*/*.py 的 router 函数。
"""
from __future__ import annotations

import functools
import inspect
from typing import Any, Callable

from pydantic import BaseModel

from src.common.response.response_schema import Response, response_base


def to_schema(raw: Any, schema: type[BaseModel] | None) -> Any:
    """ORM → Pydantic 自动转换。支持 None / dict / BaseModel / list / ORM 实例。"""
    if raw is None or schema is None:
        return raw
    if isinstance(raw, BaseModel):
        return raw
    if isinstance(raw, list):
        return [schema.model_validate(item) for item in raw]
    return schema.model_validate(raw)


def api_response(schema: Any = None) -> Callable:
    """装饰器：把 controller 函数返回值包装为 Response[T]。

    支持 sync / async 函数。业务异常直接抛出，由全局 exception handler 处理。
    """

    def decorator(fn: Callable) -> Callable:
        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Response:
                raw = await fn(*args, **kwargs)
                payload = to_schema(raw, schema)
                return response_base.success(data=payload)

            return async_wrapper

        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Response:
            raw = fn(*args, **kwargs)
            payload = to_schema(raw, schema)
            return response_base.success(data=payload)

        return sync_wrapper

    return decorator
