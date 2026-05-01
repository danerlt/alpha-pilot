"""MarketDataService 单测（mock adapter）。"""
from __future__ import annotations

import os

from datetime import datetime, timedelta, timezone
from typing import Literal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.events.outbox import OutboxWriter
from src.execution.exchange.adapter import ExchangeAdapter
from src.execution.exchange.types import Kline, OrderRequest, OrderResult, Ticker
from src.execution.market.data import MarketDataService
from src.models import Base, Candle, EventOutbox


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", os.environ.get("TEST_DATABASE_URL", os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


class _MockAdapter(ExchangeAdapter):
    """给 MarketDataService 用的最小 ExchangeAdapter stub。"""

    def __init__(self, klines: list[Kline]):
        self._klines = klines

    @property
    def trading_mode(self) -> Literal["testnet", "mainnet"]:
        return "testnet"

    def get_ticker(self, symbol: str) -> Ticker:
        raise NotImplementedError

    def get_klines(self, symbol: str, timeframe: str, *, limit: int = 300,
                   end_time: int | None = None) -> list[Kline]:
        return self._klines

    def submit_order(self, request: OrderRequest) -> OrderResult:
        raise NotImplementedError

    def get_order(self, symbol: str, exchange_order_id: str) -> OrderResult:
        raise NotImplementedError

    def cancel_order(self, symbol: str, exchange_order_id: str) -> OrderResult:
        raise NotImplementedError

    def get_balance(self, asset: str) -> float:
        return 0.0


def _make_klines(n: int, *, symbol="BTCUSDT", timeframe="1h", start_price=100.0):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    out = []
    for i in range(n):
        p = start_price + i * 0.5
        out.append(Kline(
            symbol=symbol, timeframe=timeframe,
            open_time=base + timedelta(hours=i),
            open=p * 0.999, high=p * 1.002, low=p * 0.998,
            close=p, volume=1000.0 + i,
        ))
    return out


def test_fetch_and_store_writes_candles(session):
    klines = _make_klines(10)
    svc = MarketDataService(session, _MockAdapter(klines))
    n = svc.fetch_and_store(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h",
        trace_id="t1", limit=10,
    )
    assert n == 10
    assert session.execute(select(Candle)).all() != []
    rows = session.execute(select(Candle).order_by(Candle.open_time)).scalars().all()
    assert len(rows) == 10
    assert rows[0].symbol == "BTCUSDT"
    assert rows[0].account_id == 1


def test_fetch_and_store_is_idempotent(session):
    klines = _make_klines(5)
    svc = MarketDataService(session, _MockAdapter(klines))
    svc.fetch_and_store(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h", trace_id="t1", limit=5,
    )
    # 重复拉同样 K 线 → 仍然 5 行, 不重复
    svc.fetch_and_store(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h", trace_id="t2", limit=5,
    )
    rows = session.execute(select(Candle)).scalars().all()
    assert len(rows) == 5


def test_fetch_and_store_emits_outbox_events(session):
    klines = _make_klines(3)
    outbox = OutboxWriter()
    svc = MarketDataService(session, _MockAdapter(klines), outbox=outbox)
    svc.fetch_and_store(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h", trace_id="tid-1", limit=3,
    )
    session.commit()
    evts = session.execute(select(EventOutbox)).scalars().all()
    assert len(evts) == 3
    assert evts[0].event_type == "candle.closed"
    assert evts[0].payload_json["trace_id"] == "tid-1"


def test_fetch_and_store_handles_empty_adapter_result(session):
    svc = MarketDataService(session, _MockAdapter([]))
    n = svc.fetch_and_store(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h", trace_id="t", limit=10,
    )
    assert n == 0


def test_fetch_and_store_no_outbox_if_not_provided(session):
    klines = _make_klines(2)
    svc = MarketDataService(session, _MockAdapter(klines), outbox=None)
    svc.fetch_and_store(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h", trace_id="t", limit=2,
    )
    session.commit()
    assert session.execute(select(EventOutbox)).scalars().all() == []
