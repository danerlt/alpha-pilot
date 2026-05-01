"""position_monitor_worker.run_position_monitor_once 单元测试.

只测包装层装配 + commit, PositionMonitor.run_once 的核心逻辑由
backend/tests/unit/execution/test_position_monitor.py 覆盖.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.execution.exchange.adapter import ExchangeAdapter
from src.execution.exchange.types import OrderRequest, OrderResult, Ticker
from src.shared.enums import PositionStatus
from src.models import Base, Position
from src.workers.position_monitor_worker import run_position_monitor_once


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


class _StubAdapter(ExchangeAdapter):
    """所有持仓不触发 SL/TP, 价格平稳 → MonitorResult 全 0."""

    def __init__(self, *, ticker_price: float = 50_000.0):
        self._ticker_price = ticker_price

    @property
    def trading_mode(self) -> Literal["testnet", "mainnet"]:
        return "testnet"

    def get_ticker(self, symbol: str) -> Ticker:
        return Ticker(symbol=symbol, price=self._ticker_price)

    def get_klines(self, symbol, timeframe, *, limit=300, end_time=None):
        return []

    def submit_order(self, request: OrderRequest) -> OrderResult:
        return OrderResult(
            exchange_order_id="EX-NOOP",
            symbol=request.symbol, side=request.side,
            order_type=request.order_type, status="FILLED",
            requested_quantity=request.quantity,
            filled_quantity=request.quantity,
            avg_fill_price=self._ticker_price,
            client_order_id=request.client_order_id,
        )

    def get_order(self, s, oid): raise NotImplementedError
    def cancel_order(self, s, oid): raise NotImplementedError
    def get_balance(self, asset): return 10_000.0 if asset == "USDT" else 0.0


def test_no_open_positions_returns_zero_result(session, engine):
    adapter = _StubAdapter()
    result = run_position_monitor_once(
        db=session, account_id=1, trading_mode="testnet",
        adapter=adapter, max_daily_loss_pct=0.03,
    )
    assert result.stop_loss_closed == []
    assert result.take_profit_closed == []
    assert result.circuit_breaker_triggered is False


def test_run_commits_session(session, engine):
    """worker 内部应 commit, 让 SL/TP 写入及时落地."""
    # 加 1 个开仓但价格不触发, 验证 monitor.run_once 正常返回 + commit
    pos = Position(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", status=PositionStatus.OPEN.value, side="LONG",
        quantity=0.01, entry_price=50_000.0, stop_loss=49_000.0,
        take_profit=51_000.0,
        opened_at=datetime.now(tz=timezone.utc),
    )
    session.add(pos)
    session.commit()

    adapter = _StubAdapter(ticker_price=50_000.0)
    result = run_position_monitor_once(
        db=session, account_id=1, trading_mode="testnet",
        adapter=adapter, max_daily_loss_pct=0.03,
    )
    assert result.stop_loss_closed == []  # 50k > 49k SL
    assert result.take_profit_closed == []  # 50k < 51k TP

    # 持仓更新被 commit (current_price 字段被刷)
    with Session(engine) as s2:
        fresh = s2.execute(select(Position)).scalars().first()
        assert fresh is not None
        assert float(fresh.current_price or 0) == pytest.approx(50_000.0)
