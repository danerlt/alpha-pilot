"""AccountStateService 单测。"""
from __future__ import annotations

import os

from datetime import date, datetime, timezone
from typing import Literal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.execution.account.state import AccountStateService
from src.execution.exchange.adapter import ExchangeAdapter
from src.execution.exchange.types import Kline, OrderRequest, OrderResult, Ticker
from src.shared.enums import PositionStatus
from src.models import Base, Position, Trade


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


class _StubAdapter(ExchangeAdapter):
    def __init__(self, balance: float = 10_000.0):
        self._balance = balance

    @property
    def trading_mode(self) -> Literal["testnet", "mainnet"]:
        return "testnet"
    def get_ticker(self, s): raise NotImplementedError
    def get_klines(self, s, t, **kw): raise NotImplementedError
    def submit_order(self, r): raise NotImplementedError
    def get_order(self, s, oid): raise NotImplementedError
    def cancel_order(self, s, oid): raise NotImplementedError
    def get_balance(self, asset: str) -> float:
        return self._balance if asset == "USDT" else 0.0


def test_sync_snapshot_no_positions(session):
    svc = AccountStateService(session, _StubAdapter(balance=10_000.0))
    snap = svc.sync_snapshot(account_id=1, trading_mode="testnet")
    assert float(snap.available_balance_usdt) == 10_000.0
    assert float(snap.total_balance_usdt) == 10_000.0
    assert float(snap.unrealized_pnl) == 0.0
    assert float(snap.daily_pnl) == 0.0


def test_sync_snapshot_aggregates_open_positions(session):
    session.add(Position(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", status=PositionStatus.OPEN.value, side="LONG",
        quantity=0.01, entry_price=50_000.0, stop_loss=49_000.0,
        current_price=51_000.0, unrealized_pnl=10.0, unrealized_pnl_pct=0.02,
        opened_at=datetime.now(tz=timezone.utc),
    ))
    session.flush()

    svc = AccountStateService(session, _StubAdapter(balance=5_000.0))
    snap = svc.sync_snapshot(account_id=1, trading_mode="testnet")
    # market_value = 0.01 * 51_000 = 510
    # total = 5_000 + 510 = 5_510
    assert abs(float(snap.total_balance_usdt) - 5_510.0) < 0.01
    assert float(snap.unrealized_pnl) == 10.0


def test_sync_snapshot_aggregates_today_trades_pnl(session):
    session.add(Trade(
        account_id=1, trading_mode="testnet",
        position_id=1,
        symbol="BTCUSDT", side="LONG",
        entry_price=50_000.0, exit_price=50_500.0,
        quantity=0.01, pnl=5.0, pnl_pct=0.01,
        opened_at=datetime.now(tz=timezone.utc),
        closed_at=datetime.now(tz=timezone.utc),
        exit_reason="take_profit",
    ))
    session.flush()

    svc = AccountStateService(session, _StubAdapter(balance=10_000.0))
    snap = svc.sync_snapshot(account_id=1, trading_mode="testnet")
    assert float(snap.daily_pnl) == 5.0
    # daily_pnl_pct = 5 / 10000
    assert abs(float(snap.daily_pnl_pct) - 0.0005) < 1e-6


def test_get_current_balance_usdt(session):
    svc = AccountStateService(session, _StubAdapter(balance=7_777.0))
    svc.sync_snapshot(account_id=1, trading_mode="testnet")
    assert svc.get_current_balance_usdt(account_id=1, trading_mode="testnet") == 7_777.0


def test_get_daily_pnl_returns_zeros_when_no_snapshot(session):
    svc = AccountStateService(session, _StubAdapter())
    pnl, pct = svc.get_daily_pnl(account_id=1, trading_mode="testnet")
    assert pnl == 0.0
    assert pct == 0.0


def test_get_daily_pnl_reads_latest_snapshot(session):
    svc = AccountStateService(session, _StubAdapter(balance=10_000.0))
    # 第一个 snapshot
    svc.sync_snapshot(account_id=1, trading_mode="testnet")
    # 加一笔今日 trade 后再 sync
    session.add(Trade(
        account_id=1, trading_mode="testnet",
        position_id=99,
        symbol="ETHUSDT", side="LONG",
        entry_price=3000, exit_price=3030,
        quantity=1.0, pnl=30.0, pnl_pct=0.01,
        opened_at=datetime.now(tz=timezone.utc),
        closed_at=datetime.now(tz=timezone.utc),
        exit_reason="ai_close",
    ))
    session.flush()
    svc.sync_snapshot(account_id=1, trading_mode="testnet")

    pnl, pct = svc.get_daily_pnl(account_id=1, trading_mode="testnet")
    assert pnl == 30.0
    assert abs(pct - 0.003) < 1e-6
