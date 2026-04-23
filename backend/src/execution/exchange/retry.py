"""Retry decorator for exchange calls with exponential backoff + jitter.

Two custom exceptions draw the retriable / non-retriable boundary:

- ExchangeTemporarilyUnavailable: 5xx, 429, timeout, connection error
  → `with_retry` will sleep and try again (up to `retries` times)
- PermanentExchangeError: 4xx (except 429), malformed request
  → `with_retry` re-raises immediately without retrying

Callers (e.g. BinanceAdapter) decide which to raise by inspecting the underlying
exchange error code. This keeps the retry policy domain-agnostic.
"""
from __future__ import annotations

import functools
import logging
import random
import time
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ExchangeTemporarilyUnavailable(Exception):
    """Retriable — caller may retry with backoff."""


class PermanentExchangeError(Exception):
    """Non-retriable — caller must fix the request."""


def with_retry(
    *,
    retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    jitter: float = 0.2,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator: exponential backoff with jitter on ExchangeTemporarilyUnavailable.

    `retries` is the number of retries AFTER the initial attempt, so with
    retries=3 the function may be invoked up to 4 times total.
    """
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            attempt = 0
            while True:
                try:
                    return fn(*args, **kwargs)
                except PermanentExchangeError:
                    raise
                except ExchangeTemporarilyUnavailable:
                    if attempt >= retries:
                        logger.warning(
                            "giving up on %s after %d attempts", fn.__name__, attempt + 1
                        )
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    delay += random.uniform(0, delay * jitter)
                    logger.info(
                        "retry %s attempt %d after %.2fs", fn.__name__, attempt + 1, delay
                    )
                    time.sleep(delay)
                    attempt += 1
        return wrapper
    return decorator
