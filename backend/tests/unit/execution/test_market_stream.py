"""MarketStreamManager 单测 — 归一化/节流/订阅扇出 (handoff P2b)。"""
from __future__ import annotations

import asyncio

import pytest

from src.services.execution.market_stream import (
    MarketStreamManager,
    _normalize_stream_message,
)

# ── 归一化纯函数 ─────────────────────────────────────────────────────────

_RAW_TICKER = {
    "stream": "btcusdt@ticker",
    "data": {
        "e": "24hrTicker", "s": "BTCUSDT", "c": "50000.5", "P": "-2.15",
        "h": "51000", "l": "49000", "v": "12345.6", "q": "617280000",
        "E": 1751700000000,
    },
}
_RAW_DEPTH = {
    "stream": "btcusdt@depth10@100ms",
    "data": {
        "bids": [["49999.9", "1.2"], ["49999.0", "0.5"]],
        "asks": [["50000.1", "0.8"], ["50001.0", "2.0"]],
    },
}
_RAW_TRADE = {
    "stream": "btcusdt@trade",
    "data": {
        "e": "trade", "s": "BTCUSDT", "p": "50000.2", "q": "0.01",
        "m": True, "T": 1751700000123,
    },
}


def test_normalize_ticker():
    kind, payload = _normalize_stream_message("BTCUSDT", _RAW_TICKER)
    assert kind == "ticker"
    assert payload["last_price"] == 50000.5
    assert payload["price_change_pct"] == pytest.approx(-0.0215)
    assert payload["high_24h"] == 51000.0
    assert payload["quote_volume_24h"] == 617280000.0


def test_normalize_depth():
    kind, payload = _normalize_stream_message("BTCUSDT", _RAW_DEPTH)
    assert kind == "depth"
    assert payload["bids"][0] == [49999.9, 1.2]
    assert payload["asks"][1] == [50001.0, 2.0]


def test_normalize_trade():
    kind, payload = _normalize_stream_message("BTCUSDT", _RAW_TRADE)
    assert kind == "trade"
    assert payload["price"] == 50000.2
    assert payload["side"] == "sell"  # m=True → buyer is maker → 主动卖
    assert payload["ts"] == 1751700000123


def test_normalize_unknown_stream_returns_none():
    kind, _ = _normalize_stream_message("BTCUSDT", {"stream": "btcusdt@kline_1m", "data": {}})
    assert kind is None


# ── 订阅/节流/扇出 ───────────────────────────────────────────────────────


def _fake_upstream(messages, *, hang_after=True):
    """假上游: 吐完给定消息后挂起 (模拟长连接)。"""

    async def factory(symbol: str):
        for m in messages:
            yield m
        if hang_after:
            await asyncio.Event().wait()  # 挂起直到被 cancel

    return factory


@pytest.mark.asyncio
async def test_subscriber_receives_throttled_messages():
    mgr = MarketStreamManager(
        upstream_factory=_fake_upstream([_RAW_TICKER, _RAW_DEPTH, _RAW_TRADE, _RAW_TRADE]),
        throttle_seconds=0.05,
    )
    q = await mgr.subscribe("BTCUSDT")
    try:
        got: dict[str, dict] = {}
        for _ in range(3):
            msg = await asyncio.wait_for(q.get(), timeout=2.0)
            got[msg["type"]] = msg
        assert set(got) == {"market.ticker", "market.depth", "market.trades"}
        assert got["market.ticker"]["symbol"] == "BTCUSDT"
        assert got["market.ticker"]["data"]["last_price"] == 50000.5
        # 同一窗口两笔 trade 合并成一个批次
        assert len(got["market.trades"]["data"]) == 2
    finally:
        await mgr.unsubscribe("BTCUSDT", q)
        await mgr.shutdown()


@pytest.mark.asyncio
async def test_two_subscribers_both_receive():
    mgr = MarketStreamManager(
        upstream_factory=_fake_upstream([_RAW_TICKER]),
        throttle_seconds=0.05,
    )
    q1 = await mgr.subscribe("BTCUSDT")
    q2 = await mgr.subscribe("BTCUSDT")
    try:
        m1 = await asyncio.wait_for(q1.get(), timeout=2.0)
        m2 = await asyncio.wait_for(q2.get(), timeout=2.0)
        assert m1["type"] == m2["type"] == "market.ticker"
    finally:
        await mgr.unsubscribe("BTCUSDT", q1)
        await mgr.unsubscribe("BTCUSDT", q2)
        await mgr.shutdown()


@pytest.mark.asyncio
async def test_last_unsubscribe_tears_down_hub():
    mgr = MarketStreamManager(
        upstream_factory=_fake_upstream([_RAW_TICKER]),
        throttle_seconds=0.05,
    )
    q = await mgr.subscribe("BTCUSDT")
    assert mgr.active_symbols() == ["BTCUSDT"]
    await mgr.unsubscribe("BTCUSDT", q)
    assert mgr.active_symbols() == []
    await mgr.shutdown()


@pytest.mark.asyncio
async def test_slow_subscriber_drops_instead_of_blocking():
    """队列满时丢消息, 不抛异常不阻塞 flusher。"""
    many = [_RAW_TICKER] * 5
    mgr = MarketStreamManager(
        upstream_factory=_fake_upstream(many),
        throttle_seconds=0.01,
        queue_maxsize=1,
    )
    q = await mgr.subscribe("BTCUSDT")
    try:
        await asyncio.sleep(0.2)  # 不消费, 让 flusher 多轮触发
        assert q.qsize() <= 1  # 满了就丢, 不会溢出
    finally:
        await mgr.unsubscribe("BTCUSDT", q)
        await mgr.shutdown()
