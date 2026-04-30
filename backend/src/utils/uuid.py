"""UUID 工具。"""
from __future__ import annotations

from uuid import uuid4


def get_uuid_without_hyphen() -> str:
    """生成 32 字符 hex（无横线）的 UUID4。

    用于：
    - HTTP request_id（asgi-correlation-id middleware 的 generator）
    - 历史业务键（部分旧表保留）
    """
    return uuid4().hex
