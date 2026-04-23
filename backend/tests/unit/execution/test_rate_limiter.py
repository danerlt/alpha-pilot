from __future__ import annotations

import time

import pytest

from src.execution.exchange.rate_limiter import RateLimiter, RateLimitExceeded


def test_bucket_allows_up_to_capacity():
    limiter = RateLimiter(capacity=5, refill_per_second=0)  # no refill
    for _ in range(5):
        limiter.acquire(1, blocking=False)
    with pytest.raises(RateLimitExceeded):
        limiter.acquire(1, blocking=False)


def test_bucket_refills_over_time():
    limiter = RateLimiter(capacity=2, refill_per_second=10)  # refills very fast
    limiter.acquire(2, blocking=False)
    time.sleep(0.25)  # should refill ~2.5 tokens
    limiter.acquire(1, blocking=False)


def test_blocking_acquire_waits_until_refill():
    limiter = RateLimiter(capacity=1, refill_per_second=10)
    limiter.acquire(1, blocking=False)
    start = time.monotonic()
    limiter.acquire(1, blocking=True)
    elapsed = time.monotonic() - start
    assert 0.05 <= elapsed <= 0.5, f"expected ~0.1s wait, got {elapsed:.3f}"


def test_acquire_raises_if_request_exceeds_capacity():
    limiter = RateLimiter(capacity=5, refill_per_second=1)
    with pytest.raises(ValueError):
        limiter.acquire(10, blocking=False)


def test_invalid_capacity_raises():
    with pytest.raises(ValueError):
        RateLimiter(capacity=0, refill_per_second=1)
    with pytest.raises(ValueError):
        RateLimiter(capacity=-1, refill_per_second=1)


def test_invalid_refill_raises():
    with pytest.raises(ValueError):
        RateLimiter(capacity=5, refill_per_second=-1)


def test_timeout_raises_rate_limit_exceeded():
    limiter = RateLimiter(capacity=1, refill_per_second=0.5)  # slow refill
    limiter.acquire(1, blocking=False)
    with pytest.raises(RateLimitExceeded):
        limiter.acquire(1, blocking=True, timeout=0.1)  # not enough time to refill
