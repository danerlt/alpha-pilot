"""WSConnectionManager 单测 (TEST-1 补强)。

重点回归 broadcast 的死连接自动剔除逻辑。
"""
from __future__ import annotations

import pytest

from src.services.ws_manager import WSConnectionManager


class _FakeWS:
    """最小 WebSocket 替身: send_text 可配置抛错以模拟死连接。"""

    def __init__(self, *, fail: bool = False):
        self.fail = fail
        self.sent: list[str] = []

    async def send_text(self, message: str) -> None:
        if self.fail:
            raise RuntimeError("connection closed")
        self.sent.append(message)


@pytest.mark.asyncio
async def test_add_remove_count():
    mgr = WSConnectionManager()
    a, b = _FakeWS(), _FakeWS()
    assert mgr.count == 0
    await mgr.add(a)
    await mgr.add(b)
    assert mgr.count == 2
    mgr.remove(a)
    assert mgr.count == 1
    # remove 幂等: 再删不存在的不报错
    mgr.remove(a)
    assert mgr.count == 1


@pytest.mark.asyncio
async def test_broadcast_sends_to_all_live():
    mgr = WSConnectionManager()
    a, b = _FakeWS(), _FakeWS()
    await mgr.add(a)
    await mgr.add(b)
    await mgr.broadcast("hello")
    assert a.sent == ["hello"]
    assert b.sent == ["hello"]
    assert mgr.count == 2


@pytest.mark.asyncio
async def test_broadcast_evicts_dead_connections():
    mgr = WSConnectionManager()
    live = _FakeWS()
    dead = _FakeWS(fail=True)
    await mgr.add(live)
    await mgr.add(dead)
    assert mgr.count == 2

    await mgr.broadcast("ping")

    # 死连接被剔除, 活连接仍在且收到消息
    assert mgr.count == 1
    assert live.sent == ["ping"]

    # 再次广播只剩活连接, 不再因死连接抛错
    await mgr.broadcast("ping2")
    assert live.sent == ["ping", "ping2"]
    assert mgr.count == 1
