"""跨模块复用的 datetime 小工具.

V0.1 SQLite 不持久化 timezone, 读回来的 datetime 是 naive; 跟 datetime.now(tz=utc)
做加减就会 TypeError. 统一通过 ensure_aware 把 naive 当成 UTC 处理, 让上层
`datetime - datetime` 永远成立。Postgres 列是 timestamptz, ensure_aware 是 no-op.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def ensure_aware(dt: Optional[datetime], *, default_now: bool = True) -> datetime:
    """Coerce a (possibly naive / None) datetime to a UTC-aware one.

    Args:
        dt: 原始时间; 可能是 naive datetime / aware datetime / None
        default_now: dt 是 None 时, True → 返回 datetime.now(tz=utc), False → 抛 ValueError

    Returns:
        永远是 timezone.utc 的 aware datetime
    """
    if dt is None:
        if default_now:
            return datetime.now(tz=timezone.utc)
        raise ValueError("ensure_aware called with None and default_now=False")
    if dt.tzinfo is not None:
        return dt
    return dt.replace(tzinfo=timezone.utc)


def utcnow() -> datetime:
    """datetime.now(tz=timezone.utc) 的简写, 单一调用避免漏写 tz."""
    return datetime.now(tz=timezone.utc)
