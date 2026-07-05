"""/api/market/* API 层测试。"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app import app
from src.controllers.dependencies import get_adapter, get_current_user
from src.core.exchange.adapter import ExchangeAdapter
from src.core.exchange.types import (
    FuturesMetrics,
    Kline,
    OrderRequest,
    OrderResult,
    Ticker,
    Ticker24h,
)
from src.db.session import get_db
from src.models import Base


class _StubAdapter(ExchangeAdapter):
    def get_ticker(self, symbol: str) -> Ticker:
        return Ticker(symbol=symbol, price=50_000.0)

    def get_klines(self, symbol, timeframe, *, limit=300, end_time=None) -> list[Kline]:
        now = datetime.now(tz=timezone.utc)
        return [
            Kline(
                symbol=symbol, timeframe=timeframe,
                open_time=now - timedelta(hours=limit - i),
                open=1.0, high=2.0, low=0.5, close=1.5, volume=10.0,
            )
            for i in range(limit)
        ]

    def get_ticker_24h(self, symbol: str) -> Ticker24h | None:
        return Ticker24h(
            symbol=symbol, last_price=50_000.0, price_change_pct=0.012,
            high_24h=51_000.0, low_24h=49_000.0,
            volume_24h=123.4, quote_volume_24h=6_170_000.0,
        )

    def get_futures_metrics(self, symbol: str) -> FuturesMetrics | None:
        return FuturesMetrics(symbol=symbol, mark_price=50_010.0, funding_rate=0.0001)

    def submit_order(self, request: OrderRequest) -> OrderResult:
        raise NotImplementedError

    def get_order(self, symbol, exchange_order_id):
        raise NotImplementedError

    def cancel_order(self, symbol, exchange_order_id):
        raise NotImplementedError

    def get_balance(self, asset: str) -> float:
        return 10_000.0

    @property
    def trading_mode(self):
        return "testnet"


@pytest.fixture
def engine():
    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def authed_client(engine):
    def _override():
        s = Session(engine)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    from types import SimpleNamespace

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="u", role="user", status="active",
    )
    app.dependency_overrides[get_adapter] = lambda: _StubAdapter()
    yield TestClient(app), engine
    app.dependency_overrides.clear()


def test_klines_returns_series(authed_client):
    cli, _ = authed_client
    r = cli.get("/api/market/klines?symbol=BTCUSDT&interval=1h&limit=50")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert len(body["data"]) == 50
    assert set(body["data"][0]) == {"open_time", "open", "high", "low", "close", "volume"}


def test_klines_rejects_bad_interval(authed_client):
    cli, _ = authed_client
    r = cli.get("/api/market/klines?symbol=BTCUSDT&interval=2h")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body["code"] == "400001"  # PARAM_ERROR


def test_market_endpoints_reject_anonymous():
    cli = TestClient(app)
    r = cli.get("/api/market/klines?symbol=BTCUSDT")
    assert r.status_code == 200
    assert r.json()["code"] == "400003"
