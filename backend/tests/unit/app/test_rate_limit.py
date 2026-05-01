"""rate_limit 单元测试.

post-Plan5 安全审计 H4: login brute-force 防护.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.controllers.rate_limit import InMemoryRateLimiter


def test_under_threshold_passes():
    rl = InMemoryRateLimiter(max_hits=3, window_seconds=10.0)
    rl.check("ip:1.2.3.4")
    rl.check("ip:1.2.3.4")
    # 没到 3 次, 不抛


def test_over_threshold_raises_429():
    rl = InMemoryRateLimiter(max_hits=3, window_seconds=10.0)
    for _ in range(3):
        rl.check("ip:1.2.3.4")
    with pytest.raises(HTTPException) as exc:
        rl.check("ip:1.2.3.4")
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers
    assert int(exc.value.headers["Retry-After"]) >= 1


def test_different_keys_independent():
    rl = InMemoryRateLimiter(max_hits=2, window_seconds=10.0)
    rl.check("ip:1")
    rl.check("ip:1")
    # ip:1 用完 quota, 但 ip:2 不受影响
    rl.check("ip:2")
    rl.check("ip:2")
    with pytest.raises(HTTPException):
        rl.check("ip:1")
    with pytest.raises(HTTPException):
        rl.check("ip:2")


def test_reset_clears_specific_key():
    rl = InMemoryRateLimiter(max_hits=2, window_seconds=10.0)
    rl.check("a")
    rl.check("a")
    with pytest.raises(HTTPException):
        rl.check("a")
    rl.reset("a")
    rl.check("a")  # 重置后 quota 恢复


def test_reset_all_clears_everything():
    rl = InMemoryRateLimiter(max_hits=1, window_seconds=10.0)
    rl.check("a")
    rl.check("b")
    rl.reset()
    rl.check("a")
    rl.check("b")


def test_window_slides_after_expiry(monkeypatch):
    """超过窗口时间后旧 hit 应被清掉, quota 恢复."""
    import src.controllers.rate_limit as rl_module

    fake_time = [0.0]
    monkeypatch.setattr(rl_module.time, "monotonic", lambda: fake_time[0])

    rl = InMemoryRateLimiter(max_hits=2, window_seconds=10.0)
    rl.check("a")  # t=0
    rl.check("a")  # t=0
    with pytest.raises(HTTPException):
        rl.check("a")

    # 时间快进 11s, 旧 hit 已过期
    fake_time[0] = 11.0
    rl.check("a")  # 应通过


def test_max_hits_zero_rejected():
    """配置错误防御: max_hits=0 应在构造时抛."""
    with pytest.raises(ValueError):
        InMemoryRateLimiter(max_hits=0, window_seconds=10.0)
