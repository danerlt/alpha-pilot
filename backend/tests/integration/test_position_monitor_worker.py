"""position_monitor_worker 包装层的薄测试。

PositionMonitor 自身的逻辑覆盖在 unit/execution/test_position_monitor.py;
这里只验证 wrapper commit 行为和入口可调用。
"""
from __future__ import annotations

import os

from datetime import datetime, timezone
from typing import Literal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.execution.exchange.adapter import ExchangeAdapter
from src.execution.exchange.types import Kline, OrderRequest, OrderResult, Ticker
from src.shared.enums import PositionStatus
from src.models import Base, Position, Trade
from src.workers.position_monitor_worker import run_position_monitor_once


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


class _StubAdapter(ExchangeAdapter):
    def __init__(self, ticker_price: float):
        self._p = ticker_price

    @property
    def trading_mode(self) -> Literal["testnet", "mainnet"]:
        return "testnet"
    def get_ticker(self, s): return Ticker(symbol=s, price=self._p)
    def get_klines(self, s, t, **kw): raise NotImplementedError
    def submit_order(self, r):
        return OrderResult(
            exchange_order_id="EX", symbol=r.symbol, side=r.side,
            order_type=r.order_type, status="FILLED",
            requested_quantity=r.quantity, filled_quantity=r.quantity,
            avg_fill_price=self._p, client_order_id=r.client_order_id,
        )
    def get_order(self, s, oid): raise NotImplementedError
    def cancel_order(self, s, oid): raise NotImplementedError
    def get_balance(self, asset): return 10_000.0


def test_wrapper_runs_and_commits(session):
    pos = Position(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", status=PositionStatus.OPEN.value, side="LONG",
        quantity=0.01, entry_price=50_000.0, stop_loss=49_500.0,
        opened_at=datetime.now(tz=timezone.utc),
    )
    session.add(pos)
    session.flush()

    adapter = _StubAdapter(ticker_price=49_400.0)  # 跌穿 SL
    result = run_position_monitor_once(
        db=session, account_id=1, trading_mode="testnet",
        adapter=adapter,
    )
    assert pos.id in result.stop_loss_closed
    # commit 后 trades 行存在
    refreshed = session.get(Position, pos.id)
    assert refreshed.status == PositionStatus.CLOSED.value


def test_wrapper_no_open_positions(session):
    adapter = _StubAdapter(ticker_price=50_000.0)
    result = run_position_monitor_once(
        db=session, account_id=1, trading_mode="testnet",
        adapter=adapter,
    )
    assert result.prices_updated == 0
    assert result.stop_loss_closed == []
