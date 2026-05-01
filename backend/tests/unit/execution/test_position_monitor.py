"""PositionMonitor 单测。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.execution.account.state import AccountStateService
from src.execution.exchange.adapter import ExchangeAdapter
from src.execution.exchange.types import Kline, OrderRequest, OrderResult, Ticker
from src.execution.monitor.position_monitor import PositionMonitor
from src.execution.orders.executor import OrderExecutor
from src.shared.enums import PositionStatus
from src.models import Base, Position, RiskEvent, Trade


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


class _StubAdapter(ExchangeAdapter):
    def __init__(self, *, ticker_price: float = 100.0, balance: float = 10_000.0):
        self.ticker_price = ticker_price
        self._balance = balance

    @property
    def trading_mode(self) -> Literal["testnet", "mainnet"]:
        return "testnet"
    def get_ticker(self, symbol: str) -> Ticker:
        return Ticker(symbol=symbol, price=self.ticker_price)
    def get_klines(self, s, t, **kw): raise NotImplementedError
    def submit_order(self, req: OrderRequest) -> OrderResult:
        return OrderResult(
            exchange_order_id="EX-CLOSE",
            symbol=req.symbol, side=req.side, order_type=req.order_type,
            status="FILLED", requested_quantity=req.quantity,
            filled_quantity=req.quantity, avg_fill_price=self.ticker_price,
            client_order_id=req.client_order_id,
        )
    def get_order(self, s, oid): raise NotImplementedError
    def cancel_order(self, s, oid): raise NotImplementedError
    def get_balance(self, asset): return self._balance


def _seed_open_position(session, *, sl=49000.0, tp=51000.0, entry=50000.0, qty=0.01):
    p = Position(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", status=PositionStatus.OPEN.value, side="LONG",
        quantity=qty, entry_price=entry, stop_loss=sl, take_profit=tp,
        opened_at=datetime.now(tz=timezone.utc),
    )
    session.add(p)
    session.flush()
    return p


def _build(session, *, ticker_price: float):
    adapter = _StubAdapter(ticker_price=ticker_price)
    executor = OrderExecutor(session, adapter)
    account = AccountStateService(session, adapter)
    return PositionMonitor(session, adapter, executor, account)


def test_no_positions_runs_clean(session):
    mon = _build(session, ticker_price=50_000.0)
    out = mon.run_once(account_id=1, trading_mode="testnet")
    assert out.prices_updated == 0
    assert out.stop_loss_closed == []
    assert out.take_profit_closed == []
    assert out.circuit_breaker_triggered is False


def test_price_refresh_on_open_position(session):
    pos = _seed_open_position(session)
    mon = _build(session, ticker_price=50_500.0)
    out = mon.run_once(account_id=1, trading_mode="testnet")
    assert out.prices_updated == 1
    refreshed = session.get(Position, pos.id)
    assert float(refreshed.current_price) == 50_500.0
    # 未实现 PnL = (50500 - 50000) * 0.01 = 5
    assert abs(float(refreshed.unrealized_pnl) - 5.0) < 1e-6


def test_stop_loss_triggers_close(session):
    pos = _seed_open_position(session, sl=49500.0, tp=51000.0)
    mon = _build(session, ticker_price=49_400.0)  # 跌穿 SL
    out = mon.run_once(account_id=1, trading_mode="testnet")
    assert pos.id in out.stop_loss_closed
    refreshed = session.get(Position, pos.id)
    assert refreshed.status == PositionStatus.CLOSED.value
    # Trade 已写入
    trades = session.execute(select(Trade)).scalars().all()
    assert len(trades) == 1
    assert trades[0].exit_reason == "stop_loss"
    # RiskEvent 已记录
    events = session.execute(
        select(RiskEvent).where(RiskEvent.event_type == "STOP_LOSS_HIT")
    ).scalars().all()
    assert len(events) == 1


def test_take_profit_triggers_close(session):
    pos = _seed_open_position(session, sl=49000.0, tp=51000.0)
    mon = _build(session, ticker_price=51_100.0)  # 触及 TP
    out = mon.run_once(account_id=1, trading_mode="testnet")
    assert pos.id in out.take_profit_closed
    refreshed = session.get(Position, pos.id)
    assert refreshed.status == PositionStatus.CLOSED.value


def test_circuit_breaker_fires_on_high_daily_loss(session):
    # 写一个今天的 trade 制造亏损
    trade = Trade(
        account_id=1, trading_mode="testnet", position_id=999,
        symbol="ETHUSDT", side="LONG",
        entry_price=3000, exit_price=2700, quantity=10.0,
        pnl=-3000.0, pnl_pct=-0.10,
        opened_at=datetime.now(tz=timezone.utc),
        closed_at=datetime.now(tz=timezone.utc),
        exit_reason="stop_loss",
    )
    session.add(trade)
    session.flush()

    mon = _build(session, ticker_price=50_000.0)
    # 先 sync snapshot 让 daily_pnl_pct 真实更新
    mon._account.sync_snapshot(account_id=1, trading_mode="testnet")
    out = mon.run_once(account_id=1, trading_mode="testnet", max_daily_loss_pct=0.03)
    assert out.circuit_breaker_triggered is True
    events = session.execute(
        select(RiskEvent).where(RiskEvent.event_type == "CIRCUIT_BREAKER_TRIGGERED")
    ).scalars().all()
    assert len(events) >= 1


def test_no_circuit_breaker_when_loss_below_threshold(session):
    mon = _build(session, ticker_price=50_000.0)
    out = mon.run_once(account_id=1, trading_mode="testnet")
    assert out.circuit_breaker_triggered is False


def test_circuit_breaker_dedupes_within_same_day(session):
    """post-Plan5 codereview Risk #1: 监控每 10s 跑一次, 一旦
    daily_pnl_pct 持续低于阈值, 第 N 次调用必须复用第 1 次写的 RiskEvent,
    不再插新行 — 否则操作员永远 resolve 不完."""
    trade = Trade(
        account_id=1, trading_mode="testnet", position_id=999,
        symbol="ETHUSDT", side="LONG",
        entry_price=3000, exit_price=2700, quantity=10.0,
        pnl=-3000.0, pnl_pct=-0.10,
        opened_at=datetime.now(tz=timezone.utc),
        closed_at=datetime.now(tz=timezone.utc),
        exit_reason="stop_loss",
    )
    session.add(trade)
    session.flush()

    mon = _build(session, ticker_price=50_000.0)
    mon._account.sync_snapshot(account_id=1, trading_mode="testnet")

    # 跑 5 次模拟监控连续触发
    for _ in range(5):
        out = mon.run_once(
            account_id=1, trading_mode="testnet", max_daily_loss_pct=0.03,
        )
        assert out.circuit_breaker_triggered is True

    # 5 次只应写 1 条 risk_event (其余被去重)
    events = session.execute(
        select(RiskEvent).where(RiskEvent.event_type == "CIRCUIT_BREAKER_TRIGGERED")
    ).scalars().all()
    assert len(events) == 1


def test_circuit_breaker_writes_again_after_resolve(session):
    """resolve 旧熔断后再次触发应该重新写 — 操作员 resolve 表达"我看到了, 处理了"
    的语义, 仍持续亏损就该再次报警."""
    trade = Trade(
        account_id=1, trading_mode="testnet", position_id=999,
        symbol="ETHUSDT", side="LONG",
        entry_price=3000, exit_price=2700, quantity=10.0,
        pnl=-3000.0, pnl_pct=-0.10,
        opened_at=datetime.now(tz=timezone.utc),
        closed_at=datetime.now(tz=timezone.utc),
        exit_reason="stop_loss",
    )
    session.add(trade)
    session.flush()

    mon = _build(session, ticker_price=50_000.0)
    mon._account.sync_snapshot(account_id=1, trading_mode="testnet")

    mon.run_once(account_id=1, trading_mode="testnet", max_daily_loss_pct=0.03)
    # 操作员手动 resolve 第一条
    first = session.execute(
        select(RiskEvent).where(RiskEvent.event_type == "CIRCUIT_BREAKER_TRIGGERED")
    ).scalars().first()
    first.resolved = True
    session.flush()

    # 再跑一次, 应该再写一条新的 (因为已无 unresolved)
    mon.run_once(account_id=1, trading_mode="testnet", max_daily_loss_pct=0.03)
    events = session.execute(
        select(RiskEvent).where(RiskEvent.event_type == "CIRCUIT_BREAKER_TRIGGERED")
    ).scalars().all()
    assert len(events) == 2
    assert events[0].resolved is True
    assert events[1].resolved is False
