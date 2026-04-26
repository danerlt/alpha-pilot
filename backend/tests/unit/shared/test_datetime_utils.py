"""shared/datetime_utils 单测."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.shared.datetime_utils import ensure_aware, utcnow


def test_ensure_aware_passes_through_aware_datetime():
    dt = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    out = ensure_aware(dt)
    assert out is dt


def test_ensure_aware_attaches_utc_to_naive():
    naive = datetime(2026, 1, 1, 12, 0)  # 无 tzinfo
    out = ensure_aware(naive)
    assert out.tzinfo == timezone.utc
    assert out.replace(tzinfo=None) == naive


def test_ensure_aware_none_default_now():
    before = datetime.now(tz=timezone.utc)
    out = ensure_aware(None)
    after = datetime.now(tz=timezone.utc)
    assert before <= out <= after
    assert out.tzinfo == timezone.utc


def test_ensure_aware_none_no_default_raises():
    with pytest.raises(ValueError):
        ensure_aware(None, default_now=False)


def test_ensure_aware_naive_minus_aware_no_typeerror():
    """关键场景: naive - aware 原本会 TypeError, 统一后不再.
    模拟 SQLite 读回 naive datetime 的场景."""
    naive = datetime(2026, 1, 1, 12, 0)
    aware = datetime(2026, 1, 1, 13, 0, tzinfo=timezone.utc)
    delta = ensure_aware(aware) - ensure_aware(naive)
    assert delta.total_seconds() == 3600


def test_utcnow_is_aware_utc():
    out = utcnow()
    assert out.tzinfo == timezone.utc
