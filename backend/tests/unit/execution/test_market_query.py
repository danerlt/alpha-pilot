"""MarketQueryService 单测 — K线 DB/交易所取数策略 + ticker/symbols 聚合。"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.common.exception.errors import ParamsException
from src.common.enums import PositionStatus
from src.core.exchange.adapter import ExchangeAdapter
from src.core.exchange.types import Kline, OrderRequest, OrderResult, Ticker
from src.models import Base
from src.models.candle import Candle
from src.services.execution.market_query import MarketQueryService


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


class _StubAdapter(ExchangeAdapter):
    def __init__(self):
        self.get_klines_calls = 0

    def get_ticker(self, symbol: str) -> Ticker:
        return Ticker(symbol=symbol, price=50_000.0)

    def get_klines(self, symbol, timeframe, *, limit=300, end_time=None) -> list[Kline]:
        self.get_klines_calls += 1
        now = datetime.now(tz=timezone.utc)
        return [
            Kline(
                symbol=symbol, timeframe=timeframe,
                open_time=now - timedelta(hours=limit - i),
                open=1.0, high=2.0, low=0.5, close=1.5, volume=10.0,
            )
            for i in range(limit)
        ]

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


def _seed_candles(session, n: int, *, newest_age_seconds: int = 0):
    now = datetime.now(tz=timezone.utc) - timedelta(seconds=newest_age_seconds)
    for i in range(n):
        session.add(Candle(
            account_id=1, trading_mode="testnet", symbol="BTCUSDT", timeframe="1h",
            open_time=now - timedelta(hours=n - 1 - i),
            open=1, high=2, low=0.5, close=1.5, volume=10,
        ))
    session.commit()


def test_klines_rejects_bad_interval(session):
    svc = MarketQueryService(session, _StubAdapter())
    with pytest.raises(ParamsException):
        svc.get_klines(trading_mode="testnet", symbol="BTCUSDT", interval="2h", limit=10)


def test_klines_fresh_db_does_not_call_exchange(session):
    _seed_candles(session, 10, newest_age_seconds=60)  # 最新一根 1 分钟前 → 新鲜
    adapter = _StubAdapter()
    svc = MarketQueryService(session, adapter)
    rows = svc.get_klines(trading_mode="testnet", symbol="BTCUSDT", interval="1h", limit=10)
    assert adapter.get_klines_calls == 0
    assert len(rows) == 10
    # 时间正序
    assert rows[0]["open_time"] < rows[-1]["open_time"]
    assert set(rows[0]) == {"open_time", "open", "high", "low", "close", "volume"}


def test_klines_stale_db_falls_through_to_exchange(session):
    _seed_candles(session, 10, newest_age_seconds=3 * 3600)  # 3h 前 → 陈旧(>2×1h)
    adapter = _StubAdapter()
    svc = MarketQueryService(session, adapter)
    rows = svc.get_klines(trading_mode="testnet", symbol="BTCUSDT", interval="1h", limit=10)
    assert adapter.get_klines_calls == 1
    assert len(rows) == 10


def test_klines_insufficient_db_calls_exchange(session):
    _seed_candles(session, 3, newest_age_seconds=60)
    adapter = _StubAdapter()
    svc = MarketQueryService(session, adapter)
    rows = svc.get_klines(trading_mode="testnet", symbol="BTCUSDT", interval="1h", limit=10)
    assert adapter.get_klines_calls == 1
    assert len(rows) == 10


def test_klines_exchange_failure_falls_back_to_db(session):
    _seed_candles(session, 3, newest_age_seconds=60)

    class _Broken(_StubAdapter):
        def get_klines(self, *a, **kw):
            raise RuntimeError("exchange down")

    svc = MarketQueryService(session, _Broken())
    rows = svc.get_klines(trading_mode="testnet", symbol="BTCUSDT", interval="1h", limit=10)
    assert len(rows) == 3  # 降级返 DB 既有数据


class _RichAdapter(_StubAdapter):
    """带 24h/合约指标的 stub。"""

    def get_ticker_24h(self, symbol):
        from src.core.exchange.types import Ticker24h
        return Ticker24h(
            symbol=symbol, last_price=50_000.0, price_change_pct=0.012,
            high_24h=51_000.0, low_24h=49_000.0,
            volume_24h=123.4, quote_volume_24h=6_170_000.0,
        )

    def get_futures_metrics(self, symbol):
        from src.core.exchange.types import FuturesMetrics
        return FuturesMetrics(symbol=symbol, mark_price=50_010.0, funding_rate=0.0001)


def test_ticker_merges_24h_and_futures_metrics(session):
    svc = MarketQueryService(session, _RichAdapter())
    t = svc.get_ticker(symbol="BTCUSDT")
    assert t["last_price"] == 50_000.0
    assert t["price_change_pct"] == 0.012
    assert t["mark_price"] == 50_010.0
    assert t["funding_rate"] == 0.0001
    assert t["open_interest"] is None


def test_ticker_falls_back_to_spot_price_when_24h_unavailable(session):
    svc = MarketQueryService(session, _StubAdapter())  # get_ticker_24h 默认 None
    t = svc.get_ticker(symbol="BTCUSDT")
    assert t["last_price"] == 50_000.0  # 来自 get_ticker 现价
    assert t["price_change_pct"] is None
    assert t["mark_price"] is None


def test_list_symbols_aggregates_position_and_regime(session):
    from src.models.position import Position
    from src.models.regime import RegimeSnapshot
    from src.models.symbol_config import SymbolConfig

    now = datetime.now(tz=timezone.utc)
    session.add(SymbolConfig(symbol="BTCUSDT", base_asset="BTC", enabled=True, sort_order=1))
    session.add(SymbolConfig(symbol="ETHUSDT", base_asset="ETH", enabled=True, sort_order=2))
    session.add(SymbolConfig(symbol="OFFUSDT", base_asset="OFF", enabled=False))
    session.add(Position(
        account_id=1, trading_mode="testnet", symbol="BTCUSDT", status=PositionStatus.OPEN.value,
        side="LONG", quantity=0.01, entry_price=50_000.0, stop_loss=49_000.0,
        opened_at=now,
    ))
    session.add(RegimeSnapshot(
        account_id=1, trading_mode="testnet", symbol="BTCUSDT", timeframe="1h",
        snapshot_at=now, regime="trending_up", confidence=0.9,
    ))
    session.commit()

    svc = MarketQueryService(session, _RichAdapter())
    rows = svc.list_symbols(trading_mode="testnet")
    assert [r["symbol"] for r in rows] == ["BTCUSDT", "ETHUSDT"]  # 禁用的不出现
    btc = rows[0]
    assert btc["has_position"] is True
    assert btc["regime"] == "trending_up"
    assert btc["last_price"] == 50_000.0
    eth = rows[1]
    assert eth["has_position"] is False
    assert eth["regime"] is None
