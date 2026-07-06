"""/ws/market 行情 WS 代理端点测试 (handoff P2b)。"""
from __future__ import annotations

import asyncio
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.app import app
from src.models import Base
from src.models.symbol_config import SymbolConfig
from src.models.user import User
from src.services.auth import create_access_token, hash_password
from src.services.execution.market_stream import MarketStreamManager

_RAW_TICKER = {
    "stream": "btcusdt@ticker",
    "data": {
        "e": "24hrTicker", "s": "BTCUSDT", "c": "50000.5", "P": "-2.15",
        "h": "51000", "l": "49000", "v": "12345.6", "q": "617280000",
    },
}


@pytest.fixture
def env(monkeypatch):
    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        s.merge(User(
            id=1, username="wsuser", email="ws@test",
            password_hash=hash_password("test-password-12345"),
            role="user", status="active",
        ))
        s.add(SymbolConfig(symbol="BTCUSDT", base_asset="BTC", enabled=True))
        s.add(SymbolConfig(symbol="OFFUSDT", base_asset="OFF", enabled=False))
        s.commit()

    Local = sessionmaker(bind=eng, autocommit=False, autoflush=False)
    # /ws 鉴权与 /ws/market symbol 校验都要走测试 engine
    monkeypatch.setattr("src.controllers.websocket.get_session_factory", lambda: Local)
    monkeypatch.setattr("src.controllers.websocket_market.get_session_factory", lambda: Local)

    # 注入假上游 manager (吐一条 ticker 后挂起)
    async def _fake_upstream(symbol: str):
        yield _RAW_TICKER
        await asyncio.Event().wait()

    fake_mgr = MarketStreamManager(
        upstream_factory=_fake_upstream, throttle_seconds=0.05,
    )
    monkeypatch.setattr(
        "src.controllers.websocket_market.get_market_stream_manager",
        lambda: fake_mgr,
    )
    yield TestClient(app)


def _token(user_id: int = 1) -> str:
    from src.configs.app_configs import get_app_config

    return create_access_token(
        subject=str(user_id), role="user",
        secret_key=get_app_config().APP_AUTH_SECRET_KEY,
    )


def test_market_ws_streams_normalized_ticker(env):
    cli = env
    with cli.websocket_connect(f"/ws/market?token={_token()}&symbol=BTCUSDT") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "market.ticker"
        assert msg["symbol"] == "BTCUSDT"
        assert msg["data"]["last_price"] == 50000.5


def test_market_ws_rejects_missing_token(env):
    cli = env
    from starlette.websockets import WebSocketDisconnect as WSDisc

    with pytest.raises(WSDisc) as exc_info:
        with cli.websocket_connect("/ws/market?symbol=BTCUSDT"):
            pass
    assert exc_info.value.code == 4401


def test_market_ws_rejects_disabled_symbol(env):
    cli = env
    from starlette.websockets import WebSocketDisconnect as WSDisc

    with pytest.raises(WSDisc) as exc_info:
        with cli.websocket_connect(f"/ws/market?token={_token()}&symbol=OFFUSDT"):
            pass
    assert exc_info.value.code == 4404


def test_market_ws_rejects_unknown_symbol(env):
    cli = env
    from starlette.websockets import WebSocketDisconnect as WSDisc

    with pytest.raises(WSDisc) as exc_info:
        with cli.websocket_connect(f"/ws/market?token={_token()}&symbol=NOPEUSDT"):
            pass
    assert exc_info.value.code == 4404


def test_market_ws_accepts_httponly_cookie(env):
    """浏览器验收修复: 无 ?token= 时回退 ap_token cookie (前端刷新后场景)。"""
    cli = env
    cli.cookies.set("ap_token", _token())
    with cli.websocket_connect("/ws/market?symbol=BTCUSDT") as ws:
        msg = ws.receive_json()
        assert msg["type"].startswith("market.")
