"""通用分页响应 schema。"""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    """泛型分页响应。

    字段语义：
    - items: 当前页数据列表
    - total: 总条数
    - page_index: 当前页码（1-based）
    - page_size: 每页大小
    - pages: 总页数 = ceil(total / page_size)
    """

    items: list[T] = Field(default_factory=list, description="当前页数据列表")
    total: int = Field(default=0, description="总条数")
    page_index: int = Field(default=1, description="当前页码（1-based）")
    page_size: int = Field(default=20, description="每页大小")
    pages: int = Field(default=0, description="总页数 = ceil(total / page_size)")
