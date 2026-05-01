"""OrderExecutor 单测。"""
from __future__ import annotations

import os

from datetime import datetime, timezone
from typing import Literal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.services.events.outbox import OutboxWriter
from src.core.exchange.adapter import ExchangeAdapter
from src.core.exchange.retry import ExchangeTemporarilyUnavailable
from src.core.exchange.types import Kline, OrderRequest, OrderResult, Ticker
from src.services.execution.order_executor import OrderExecutor, make_trace_id
from src.shared.enums import OrderStatus, PositionStatus
from src.models import Base, EventOutbox, Order, Position, Trade
from src.strategy.proposal import DecisionProposal


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


class _StubAdapter(ExchangeAdapter):
    def __init__(self, *, fail_with: Exception | None = None,
                 fill_price: float | None = None,
                 fill_qty: float | None = None,
                 status: str = "FILLED"):
        self._fail = fail_with
        self._fill_price = fill_price
        self._fill_qty = fill_qty
        self._status = status
        self.submit_calls: list[OrderRequest] = []

    @property
    def trading_mode(self) -> Literal["testnet", "mainnet"]:
        return "testnet"
    def get_ticker(self, s): raise NotImplementedError
    def get_klines(self, s, t, **kw): raise NotImplementedError
    def get_order(self, s, oid): raise NotImplementedError
    def cancel_order(self, s, oid): raise NotImplementedError
    def get_balance(self, asset): return 0.0

    def submit_order(self, req: OrderRequest) -> OrderResult:
        self.submit_calls.append(req)
        if self._fail is not None:
            raise self._fail
        return OrderResult(
            exchange_order_id="EX12345",
            symbol=req.symbol, side=req.side,
            order_type=req.order_type, status=self._status,
            requested_quantity=req.quantity,
            filled_quantity=self._fill_qty if self._fill_qty is not None else req.quantity,
            avg_fill_price=self._fill_price if self._fill_price is not None else (req.price or 50000.0),
            client_order_id=req.client_order_id,
        )


def _proposal_open() -> DecisionProposal:
    return DecisionProposal(
        account_id=1, symbol="BTCUSDT", timeframe="1h",
        action="OPEN_LONG", confidence=0.7,
        entry_type="MARKET", entry_price=50000.0,
        stop_loss=49000.0, take_profit=52000.0,
        position_size_pct=0.10,
        strategy_mode="ai_trend", source="ai_trader",
    )


def test_open_long_writes_order_and_position(session):
    adapter = _StubAdapter(fill_price=50_000.0)
    executor = OrderExecutor(session, adapter)
    res = executor.open_long(
        proposal=_proposal_open(), decision_id=42,
        account_id=1, trading_mode="testnet",
        available_usdt=10_000.0, current_price=50_000.0,
    )
    assert res is not None
    order, position = res
    assert order.status == OrderStatus.FILLED.value
    assert order.symbol == "BTCUSDT"
    # quantity = 10000 * 0.10 / 50000 = 0.02
    assert abs(float(order.quantity) - 0.02) < 1e-8
    assert position.status == PositionStatus.OPEN.value
    assert float(position.entry_price) == 50_000.0
    assert order.position_id == position.id


def test_open_long_is_idempotent_on_same_decision(session):
    adapter = _StubAdapter(fill_price=50_000.0)
    executor = OrderExecutor(session, adapter)
    executor.open_long(
        proposal=_proposal_open(), decision_id=42,
        account_id=1, trading_mode="testnet",
        available_usdt=10_000.0, current_price=50_000.0,
    )
    # 第二次同 decision_id → 不重复下单
    executor.open_long(
        proposal=_proposal_open(), decision_id=42,
        account_id=1, trading_mode="testnet",
        available_usdt=10_000.0, current_price=50_000.0,
    )
    assert len(adapter.submit_calls) == 1
    assert session.execute(select(Order)).scalars().all().__len__() == 1


def test_open_long_handles_adapter_failure(session):
    adapter = _StubAdapter(fail_with=ExchangeTemporarilyUnavailable("network"))
    outbox = OutboxWriter()
    executor = OrderExecutor(session, adapter, outbox=outbox)
    res = executor.open_long(
        proposal=_proposal_open(), decision_id=42,
        account_id=1, trading_mode="testnet",
        available_usdt=10_000.0, current_price=50_000.0,
    )
    assert res is None
    order = session.execute(select(Order)).scalars().first()
    assert order.status == OrderStatus.FAILED.value
    # OrderFailed 事件已发
    session.commit()
    evts = session.execute(
        select(EventOutbox).where(EventOutbox.event_type == "order.failed")
    ).scalars().all()
    assert len(evts) == 1


def test_open_long_emits_outbox_events_when_outbox_provided(session):
    adapter = _StubAdapter(fill_price=50_000.0)
    outbox = OutboxWriter()
    executor = OrderExecutor(session, adapter, outbox=outbox)
    executor.open_long(
        proposal=_proposal_open(), decision_id=42,
        account_id=1, trading_mode="testnet",
        available_usdt=10_000.0, current_price=50_000.0,
    )
    session.commit()
    evt_types = [
        e.event_type
        for e in session.execute(select(EventOutbox).order_by(EventOutbox.id)).scalars().all()
    ]
    assert "order.submitted" in evt_types
    assert "order.filled" in evt_types
    assert "position.opened" in evt_types


def test_close_long_writes_trade_and_marks_position_closed(session):
    # 先开
    adapter = _StubAdapter(fill_price=50_000.0)
    executor = OrderExecutor(session, adapter)
    _, position = executor.open_long(
        proposal=_proposal_open(), decision_id=42,
        account_id=1, trading_mode="testnet",
        available_usdt=10_000.0, current_price=50_000.0,
    )
    # 平 - exit price 高于开仓 → 盈利
    adapter._fill_price = 51_000.0
    trade = executor.close_long(
        position=position, reason="take_profit",
        decision_id=99, account_id=1, trading_mode="testnet",
    )
    assert trade is not None
    assert float(trade.exit_price) == 51_000.0
    assert float(trade.pnl) > 0
    refreshed = session.get(Position, position.id)
    assert refreshed.status == PositionStatus.CLOSED.value
    # trade event
    session.commit()
    evt_types = [
        e.event_type
        for e in session.execute(select(EventOutbox)).scalars().all()
    ]
    # 没有 outbox 注入 → 没有事件
    assert evt_types == []


def test_close_long_emits_trade_closed_event(session):
    adapter = _StubAdapter(fill_price=50_000.0)
    outbox = OutboxWriter()
    executor = OrderExecutor(session, adapter, outbox=outbox)
    _, position = executor.open_long(
        proposal=_proposal_open(), decision_id=42,
        account_id=1, trading_mode="testnet",
        available_usdt=10_000.0, current_price=50_000.0,
    )
    adapter._fill_price = 50_500.0
    executor.close_long(
        position=position, reason="ai_close",
        decision_id=43, account_id=1, trading_mode="testnet",
    )
    session.commit()
    evt_types = [
        e.event_type
        for e in session.execute(select(EventOutbox)).scalars().all()
    ]
    assert "position.closed" in evt_types
    assert "trade.closed" in evt_types


def test_make_trace_id_is_deterministic_per_decision_action():
    a = make_trace_id(42, "BTCUSDT", "OPEN_LONG")
    b = make_trace_id(42, "BTCUSDT", "OPEN_LONG")
    c = make_trace_id(43, "BTCUSDT", "OPEN_LONG")
    assert a == b
    assert a != c
    assert len(a) == 32


def test_close_long_skips_when_already_closed_idempotently(session):
    adapter = _StubAdapter(fill_price=50_000.0)
    executor = OrderExecutor(session, adapter)
    _, position = executor.open_long(
        proposal=_proposal_open(), decision_id=42,
        account_id=1, trading_mode="testnet",
        available_usdt=10_000.0, current_price=50_000.0,
    )
    executor.close_long(
        position=position, reason="ai_close", decision_id=43,
        account_id=1, trading_mode="testnet",
    )
    # 第二次 close 同 position + decision → 返回 None (trace_id 已存在)
    res = executor.close_long(
        position=position, reason="ai_close", decision_id=43,
        account_id=1, trading_mode="testnet",
    )
    assert res is None
