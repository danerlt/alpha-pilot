"""Token bucket rate limiter. Thread-safe via threading.Lock.

Binance REST weight limit is 1200 per minute → capacity=1200, refill=20/s.
Binance also has a 10s-level cap (~300 weight) — not modeled here; stack a
second RateLimiter in front if you need it.
"""
from __future__ import annotations

import threading
import time


class RateLimitExceeded(Exception):
    """Raised when non-blocking acquire can't satisfy the request."""


class RateLimiter:
    def __init__(self, capacity: int, refill_per_second: float):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_per_second < 0:
            raise ValueError("refill_per_second must be non-negative")
        self._capacity = capacity
        self._refill = refill_per_second
        self._tokens = float(capacity)
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def _refill_tokens_locked(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last
        self._tokens = min(self._capacity, self._tokens + elapsed * self._refill)
        self._last = now

    def acquire(self, tokens: int = 1, *, blocking: bool = True, timeout: float | None = None) -> None:
        if tokens > self._capacity:
            raise ValueError(f"request {tokens} exceeds capacity {self._capacity}")
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            with self._lock:
                self._refill_tokens_locked()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                if not blocking:
                    raise RateLimitExceeded(
                        f"need {tokens} tokens, have {self._tokens:.2f}"
                    )
                need = tokens - self._tokens
                wait_s = need / self._refill if self._refill > 0 else 0.05
            if deadline is not None and time.monotonic() + wait_s > deadline:
                raise RateLimitExceeded("timeout waiting for tokens")
            time.sleep(min(wait_s, 0.1))
