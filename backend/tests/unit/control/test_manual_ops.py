"""ManualOpsService 单测。"""
from __future__ import annotations

import os

from datetime import datetime, timezone
from typing import Literal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.services.manual_ops import ManualOpsService
from src.core.exchange.adapter import ExchangeAdapter
from src.core.exchange.types import OrderRequest, OrderResult, Ticker
from src.shared.enums import PositionStatus
from src.models import AuditLog, Base, Position, RiskEvent, Trade


class _StubAdapter(ExchangeAdapter):
    def __init__(self, fill_price=50_000.0):
        self._p = fill_price

    @property
    def trading_mode(self) -> Literal["testnet", "mainnet"]:
        return "testnet"
    def get_ticker(self, s): return Ticker(symbol=s, price=self._p)
    def get_klines(self, s, t, **kw): raise NotImplementedError
    def submit_order(self, r: OrderRequest):
        return OrderResult(
            exchange_order_id="EX", symbol=r.symbol, side=r.side,
            order_type=r.order_type, status="FILLED",
            requested_quantity=r.quantity, filled_quantity=r.quantity,
            avg_fill_price=self._p, client_order_id=r.client_order_id,
        )
    def get_order(self, s, oid): raise NotImplementedError
    def cancel_order(self, s, oid): raise NotImplementedError
    def get_balance(self, asset): return 10_000.0


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _seed_position(session, symbol="BTCUSDT") -> Position:
    pos = Position(
        account_id=1, trading_mode="testnet",
        symbol=symbol, status=PositionStatus.OPEN.value, side="LONG",
        quantity=0.01, entry_price=50_000.0, stop_loss=49_000.0,
        opened_at=datetime.now(tz=timezone.utc),
    )
    session.add(pos)
    session.flush()
    return pos


def test_manual_close_position(session):
    pos = _seed_position(session)
    svc = ManualOpsService(session, _StubAdapter())
    trade = svc.manual_close_position(
        position_id=pos.id, reason="early_exit", operator_user_id=99,
    )
    assert trade is not None
    refreshed = session.get(Position, pos.id)
    assert refreshed.status == PositionStatus.CLOSED.value


def test_manual_close_position_writes_audit(session):
    pos = _seed_position(session)
    svc = ManualOpsService(session, _StubAdapter())
    svc.manual_close_position(
        position_id=pos.id, reason="x", operator_user_id=99,
    )
    audit = session.execute(
        select(AuditLog).where(AuditLog.action == "manual_close_position")
    ).scalars().first()
    assert audit is not None
    assert audit.user_id == 99
    assert audit.after_json["reason"] == "x"


def test_manual_close_all_closes_all_positions(session):
    p1 = _seed_position(session, symbol="BTCUSDT")
    p2 = _seed_position(session, symbol="ETHUSDT")
    svc = ManualOpsService(session, _StubAdapter())
    closed = svc.manual_close_all(
        account_id=1, trading_mode="testnet",
        reason="emergency", operator_user_id=1,
    )
    assert set(closed) == {p1.id, p2.id}
    assert all(
        session.get(Position, pid).status == PositionStatus.CLOSED.value
        for pid in closed
    )


def test_manual_resolve_circuit_breaker(session):
    event = RiskEvent(
        account_id=1, trading_mode="testnet",
        event_type="CIRCUIT_BREAKER_TRIGGERED",
        triggered_at=datetime.now(tz=timezone.utc),
        description="daily_loss",
        resolved=False,
    )
    session.add(event)
    session.flush()

    svc = ManualOpsService(session, _StubAdapter())
    ok = svc.manual_resolve_circuit_breaker(
        risk_event_id=event.id, reason="manual_check_passed",
        operator_user_id=1,
    )
    assert ok is True
    assert session.get(RiskEvent, event.id).resolved is True


def test_manual_close_position_returns_none_when_already_closed(session):
    pos = _seed_position(session)
    pos.status = PositionStatus.CLOSED.value
    session.flush()
    svc = ManualOpsService(session, _StubAdapter())
    trade = svc.manual_close_position(
        position_id=pos.id, reason="x", operator_user_id=1,
    )
    assert trade is None
