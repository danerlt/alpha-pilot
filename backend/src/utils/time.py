"""时间工具。强制北京时间（naive datetime, UTC+8）。

约定：
- DB 存储用 naive datetime，语义为北京时间
- 不在 ORM 层做 tz conversion，业务层全部用 ``TimeUtils.now()`` 取当下时间
- 与现有 ``src.shared.datetime_utils`` 行为一致；迁移路径保留兼容 import
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


class TimeUtils:
    """北京时间工具集。"""

    @staticmethod
    def now() -> datetime:
        """返回当前北京时间（UTC+8，naive datetime）。"""
        return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=8)

    @staticmethod
    def utcnow() -> datetime:
        """返回当前 UTC 时间（naive）。"""
        return datetime.now(timezone.utc).replace(tzinfo=None)
