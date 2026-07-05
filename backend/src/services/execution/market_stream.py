"""MarketStreamManager — Binance WS 行情代理 (handoff P2b / webapp 架构 B2)。

盘口与逐笔**不落库**, 纯代理转发:
  Binance combined stream ({sym}@ticker / {sym}@depth10@100ms / {sym}@trade)
    → per-symbol hub (保留每类最新 + trade 批次)
    → flusher 每 throttle_seconds(≥250ms) 扇出给订阅者 asyncio.Queue
    → /ws/market 端点 pump 给客户端

慢客户端保护: 订阅队列有界, 满了直接丢消息, 绝不阻塞 flusher。
无订阅者时拆除上游连接 (省 Binance 连接配额)。
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable

logger = logging.getLogger(__name__)

_TRADE_BATCH_MAX = 20

_KIND_TO_TYPE = {
    "ticker": "market.ticker",
    "depth": "market.depth",
    "trade": "market.trades",
}


def _normalize_stream_message(
    symbol: str, raw: dict,
) -> tuple[str | None, dict[str, Any] | None]:
    """Binance combined stream 原始消息 → (kind, payload); 不认识的流返回 (None, None)。"""
    stream = raw.get("stream", "")
    data = raw.get("data", {}) or {}
    if "@ticker" in stream:
        return "ticker", {
            "last_price": float(data["c"]),
            "price_change_pct": float(data["P"]) / 100.0,
            "high_24h": float(data["h"]),
            "low_24h": float(data["l"]),
            "volume_24h": float(data["v"]),
            "quote_volume_24h": float(data["q"]),
        }
    if "@depth" in stream:
        return "depth", {
            "bids": [[float(p), float(q)] for p, q in data.get("bids", [])],
            "asks": [[float(p), float(q)] for p, q in data.get("asks", [])],
        }
    if "@trade" in stream:
        return "trade", {
            "price": float(data["p"]),
            "qty": float(data["q"]),
            # m=True: buyer is maker → 主动方是卖单
            "side": "sell" if data.get("m") else "buy",
            "ts": data.get("T"),
        }
    return None, None


async def _binance_upstream(symbol: str, *, testnet: bool) -> AsyncIterator[dict]:
    """真实上游: 连 Binance combined stream, 断线指数退避重连。"""
    import websockets

    base = (
        "wss://testnet.binance.vision/stream"
        if testnet else "wss://stream.binance.com:9443/stream"
    )
    s = symbol.lower()
    url = f"{base}?streams={s}@ticker/{s}@depth10@100ms/{s}@trade"
    backoff = 1.0
    while True:
        try:
            async with websockets.connect(url, ping_interval=20) as ws:
                logger.info("market upstream connected: %s", symbol)
                backoff = 1.0
                async for raw in ws:
                    try:
                        yield json.loads(raw)
                    except json.JSONDecodeError:
                        continue
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.warning(
                "market upstream lost for %s; reconnect in %.1fs",
                symbol, backoff, exc_info=True,
            )
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30.0)


@dataclass
class _SymbolHub:
    subscribers: set[asyncio.Queue] = field(default_factory=set)
    latest: dict[str, dict] = field(default_factory=dict)  # kind → payload
    trades: list[dict] = field(default_factory=list)  # 本窗口 trade 批次
    dirty: set[str] = field(default_factory=set)
    consume_task: asyncio.Task | None = None
    flush_task: asyncio.Task | None = None

    def store(self, kind: str, payload: dict) -> None:
        if kind == "trade":
            self.trades.append(payload)
            if len(self.trades) > _TRADE_BATCH_MAX:
                self.trades = self.trades[-_TRADE_BATCH_MAX:]
        else:
            self.latest[kind] = payload
        self.dirty.add(kind)


class MarketStreamManager:
    def __init__(
        self,
        *,
        upstream_factory: Callable[[str], AsyncIterator[dict]] | None = None,
        throttle_seconds: float = 0.25,
        queue_maxsize: int = 100,
        testnet: bool = True,
    ):
        self._upstream_factory = upstream_factory or (
            lambda symbol: _binance_upstream(symbol, testnet=testnet)
        )
        self._throttle = throttle_seconds
        self._queue_maxsize = queue_maxsize
        self._hubs: dict[str, _SymbolHub] = {}
        self._lock = asyncio.Lock()

    def active_symbols(self) -> list[str]:
        return sorted(self._hubs)

    async def subscribe(self, symbol: str) -> asyncio.Queue:
        async with self._lock:
            hub = self._hubs.get(symbol)
            if hub is None:
                hub = _SymbolHub()
                hub.consume_task = asyncio.create_task(self._consume(symbol, hub))
                hub.flush_task = asyncio.create_task(self._flush_loop(symbol, hub))
                self._hubs[symbol] = hub
            q: asyncio.Queue = asyncio.Queue(maxsize=self._queue_maxsize)
            hub.subscribers.add(q)
            return q

    async def unsubscribe(self, symbol: str, queue: asyncio.Queue) -> None:
        async with self._lock:
            hub = self._hubs.get(symbol)
            if hub is None:
                return
            hub.subscribers.discard(queue)
            if not hub.subscribers:
                await self._teardown_hub(symbol, hub)

    async def shutdown(self) -> None:
        async with self._lock:
            for symbol, hub in list(self._hubs.items()):
                await self._teardown_hub(symbol, hub)

    # ------------------------------------------------------------------

    async def _teardown_hub(self, symbol: str, hub: _SymbolHub) -> None:
        self._hubs.pop(symbol, None)
        for task in (hub.consume_task, hub.flush_task):
            if task is not None:
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):  # noqa: BLE001
                    pass
        logger.info("market hub torn down: %s", symbol)

    async def _consume(self, symbol: str, hub: _SymbolHub) -> None:
        try:
            async for raw in self._upstream_factory(symbol):
                kind, payload = _normalize_stream_message(symbol, raw)
                if kind is not None and payload is not None:
                    hub.store(kind, payload)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("market upstream consumer died for %s", symbol)

    async def _flush_loop(self, symbol: str, hub: _SymbolHub) -> None:
        while True:
            await asyncio.sleep(self._throttle)
            if not hub.dirty:
                continue
            now_ms = int(time.time() * 1000)
            messages: list[dict] = []
            for kind in sorted(hub.dirty):
                if kind == "trade":
                    if hub.trades:
                        messages.append({
                            "type": _KIND_TO_TYPE[kind], "symbol": symbol,
                            "ts": now_ms, "data": hub.trades,
                        })
                        hub.trades = []
                elif kind in hub.latest:
                    messages.append({
                        "type": _KIND_TO_TYPE[kind], "symbol": symbol,
                        "ts": now_ms, "data": hub.latest[kind],
                    })
            hub.dirty.clear()
            for q in list(hub.subscribers):
                for msg in messages:
                    try:
                        q.put_nowait(msg)
                    except asyncio.QueueFull:
                        # 慢客户端: 丢消息, 不阻塞其他订阅者
                        pass


_manager: MarketStreamManager | None = None


def get_market_stream_manager() -> MarketStreamManager:
    """api 进程内单例; testnet/mainnet 由启动配置决定。"""
    global _manager
    if _manager is None:
        from src.configs.app_configs import get_settings

        settings = get_settings()
        mode = settings.TRADING_MODE
        mode_str = mode.value if hasattr(mode, "value") else mode
        _manager = MarketStreamManager(testnet=(mode_str == "testnet"))
    return _manager
