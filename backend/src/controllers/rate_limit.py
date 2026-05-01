"""轻量内存级 rate limiter — V0.1 单进程部署够用.

post-Plan5 安全审计 H4: 防 login brute-force.

设计:
  - per-key (e.g. IP / email) 滑动窗口计数
  - 超阈值抛 HTTPException 429
  - 仅内存, 不依赖 redis (V0.1 单 APScheduler 进程部署); 多 worker 时
    必须迁到 redis-backed (V0.1.x)
  - 时间清理: 每次 check 顺手清过期 key, 不开后台线程

并发: 走 GIL 安全 (dict 操作原子), 不需要锁.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import HTTPException


class InMemoryRateLimiter:
    """滑动窗口 token bucket. key → 该 key 在 window_seconds 内的命中时间戳列表."""

    def __init__(self, *, max_hits: int, window_seconds: float):
        if max_hits <= 0:
            raise ValueError("max_hits must be > 0")
        self._max = max_hits
        self._window = window_seconds
        self._hits: dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        """记录一次命中; 超阈值抛 HTTPException 429."""
        now = time.monotonic()
        cutoff = now - self._window
        bucket = self._hits[key]
        # 清掉窗口外的旧时间戳
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self._max:
            retry_after = max(1, int(bucket[0] + self._window - now))
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests. Retry after {retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )
        bucket.append(now)

    def reset(self, key: str | None = None) -> None:
        """单测用: 清掉指定 key 或全部 key."""
        if key is None:
            self._hits.clear()
        else:
            self._hits.pop(key, None)


# 全局 limiter 实例: login 路径专用. 5 次 / 60 秒 / per-IP + per-email 双限.
# 同一 IP 同一 email 5 次失败 = 拉黑 60s. 双限可阻止"换 email 攻击同 IP"
# 和"分布式 IP 攻击同 email"两路.
login_ip_limiter = InMemoryRateLimiter(max_hits=10, window_seconds=60.0)
login_email_limiter = InMemoryRateLimiter(max_hits=5, window_seconds=60.0)
