"""/ws/market — 行情 WS 代理端点 (handoff P2b)。

协议: ws://host/ws/market?token=<jwt>&symbol=BTCUSDT
  - 一连接一 symbol (前端换 symbol 重连)
  - 鉴权同 /ws: 4401 未认证 / 4403 用户停用
  - symbol 必须在 symbol_config 且 enabled, 否则 4404 (防任意字符串透传上游)
  - 下行: {"type": "market.ticker|market.depth|market.trades", "symbol", "ts", "data"}
    (节流 ≥250ms, 不走 Response envelope)
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect, WebSocketException

from src.controllers.websocket import _verify_token, _verify_user_active
from src.db.engines import get_session_factory
from src.services.execution.market_stream import get_market_stream_manager

logger = logging.getLogger(__name__)


def _verify_symbol_enabled(symbol: str) -> None:
    """symbol 必须存在于 symbol_config 且 enabled; 否则 4404。"""
    from src.models.symbol_config import SymbolConfig

    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        row = (
            session.query(SymbolConfig)
            .filter(SymbolConfig.symbol == symbol)
            .first()
        )
        if row is None or not row.enabled:
            raise WebSocketException(code=4404, reason=f"symbol not enabled: {symbol}")
    finally:
        session.close()


async def market_websocket_endpoint(ws: WebSocket) -> None:
    # 鉴权: ?token= 优先, 回退 httpOnly cookie (ap_token) —— 前端刷新后内存
    # token 丢失但 cookie 会话仍有效, WS 必须与 REST 同源鉴权 (浏览器验收修复)
    token = ws.query_params.get("token") or ws.cookies.get("ap_token")
    user_id = _verify_token(token)
    _verify_user_active(user_id)

    symbol = (ws.query_params.get("symbol") or "").upper().strip()
    if not symbol or len(symbol) > 20 or not symbol.isalnum():
        raise WebSocketException(code=4404, reason="invalid symbol")
    _verify_symbol_enabled(symbol)

    await ws.accept()
    manager = get_market_stream_manager()
    queue = await manager.subscribe(symbol)

    async def _pump() -> None:
        while True:
            msg = await queue.get()
            await ws.send_json(msg)

    sender = asyncio.create_task(_pump())
    try:
        while True:
            # 客户端消息仅作保活, 忽略内容
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001
        logger.warning("market ws connection error for %s", symbol, exc_info=True)
    finally:
        sender.cancel()
        try:
            await sender
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass
        await manager.unsubscribe(symbol, queue)
