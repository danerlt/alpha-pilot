from __future__ import annotations

import pytest

from src.core.exchange.retry import (
    ExchangeTemporarilyUnavailable,
    PermanentExchangeError,
    with_retry,
)


def test_succeeds_on_first_try_without_retry_overhead():
    calls = {"n": 0}

    @with_retry(retries=3, base_delay=0.01)
    def ok():
        calls["n"] += 1
        return "good"

    assert ok() == "good"
    assert calls["n"] == 1


def test_retries_on_transient_then_succeeds():
    calls = {"n": 0}

    @with_retry(retries=3, base_delay=0.01)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ExchangeTemporarilyUnavailable("transient")
        return "good"

    assert flaky() == "good"
    assert calls["n"] == 3


def test_permanent_error_is_not_retried():
    calls = {"n": 0}

    @with_retry(retries=3, base_delay=0.01)
    def broken():
        calls["n"] += 1
        raise PermanentExchangeError("4xx")

    with pytest.raises(PermanentExchangeError):
        broken()
    assert calls["n"] == 1


def test_gives_up_after_max_retries():
    calls = {"n": 0}

    @with_retry(retries=2, base_delay=0.01)
    def always_fails():
        calls["n"] += 1
        raise ExchangeTemporarilyUnavailable("down")

    with pytest.raises(ExchangeTemporarilyUnavailable):
        always_fails()
    assert calls["n"] == 3  # initial + 2 retries


def test_uncaught_exception_propagates_without_retry():
    calls = {"n": 0}

    @with_retry(retries=3, base_delay=0.01)
    def random_error():
        calls["n"] += 1
        raise ValueError("something else")

    with pytest.raises(ValueError):
        random_error()
    assert calls["n"] == 1, "non-retriable exceptions should pass through"
