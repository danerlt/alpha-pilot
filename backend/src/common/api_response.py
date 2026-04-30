"""@api_response 装饰器：自动 ORM→Pydantic + response_base.success 包装。

阶段 1 引入但不强制使用；阶段 4 重构 controllers 时全面应用。
"""
from __future__ import annotations

import functools
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

    业务异常直接抛出，由全局 exception handler 处理；不在装饰器里捕获。
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Response:
            raw = fn(*args, **kwargs)
            payload = to_schema(raw, schema)
            return response_base.success(data=payload)

        return wrapper

    return decorator
