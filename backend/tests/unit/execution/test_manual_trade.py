"""ManualTradeService 单测 — 守卫预检 (handoff P2 §3.2)。"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.common.enums import PositionStatus
from src.core.exchange.adapter import ExchangeAdapter
from src.core.exchange.types import OrderRequest, OrderResult, Ticker
from src.models import Base
from src.models.account import AccountSnapshot
from src.models.account_entity import RiskProfile
from src.models.position import Position
from src.schemas.manual_order import ManualOrderCreate
from src.services.execution.manual_trade import ManualTradeService


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        s.add(RiskProfile(
            account_id=1, name="default", version=1, active=True,
            max_position_size_pct=Decimal("0.20"),
            max_daily_loss_pct=Decimal("0.03"),
            max_consecutive_losses=3,
            max_single_risk_pct=Decimal("0.01"),
            min_rr_ratio=Decimal("1.50"),
            sl_atr_min_mult=Decimal("0.50"),
            sl_atr_max_mult=Decimal("5.00"),
        ))
        s.add(AccountSnapshot(
            account_id=1, trading_mode="testnet",
            snapshot_at=datetime.now(tz=timezone.utc),
            total_balance_usdt=10_000.0, available_balance_usdt=10_000.0,
            unrealized_pnl=0, daily_pnl=0, daily_pnl_pct=0,
        ))
        s.commit()
        yield s


class _StubAdapter(ExchangeAdapter):
    def get_ticker(self, symbol: str) -> Ticker:
        return Ticker(symbol=symbol, price=50_000.0)

    def get_klines(self, symbol, timeframe, *, limit=300, end_time=None):
        return []

    def submit_order(self, request: OrderRequest) -> OrderResult:
        return OrderResult(
            exchange_order_id="EX-M1", symbol=request.symbol, side=request.side,
            order_type=request.order_type, status="FILLED",
            requested_quantity=request.quantity, filled_quantity=request.quantity,
            avg_fill_price=50_000.0, client_order_id=request.client_order_id,
        )

    def get_order(self, symbol, exchange_order_id):
        raise NotImplementedError

    def cancel_order(self, symbol, exchange_order_id):
        raise NotImplementedError

    def get_balance(self, asset: str) -> float:
        return 10_000.0

    @property
    def trading_mode(self):
        return "testnet"


def _buy(**kw) -> ManualOrderCreate:
    """合理基线: 50000 入场, SL 49900 (=0.5×ATR 200), TP 50500, 0.02 BTC ≈ 10%仓."""
    defaults = dict(
        symbol="BTCUSDT", side="BUY", type="MARKET",
        qty=0.02, sl=49_900.0, tp=50_500.0, reduce_only=False,
    )
    defaults.update(kw)
    return ManualOrderCreate(**defaults)


def _svc(session) -> ManualTradeService:
    return ManualTradeService(session, _StubAdapter())


def test_precheck_clean_buy_passes(session):
    out = _svc(session).precheck(body=_buy(), trading_mode="testnet")
    assert out.verdict == "PASS"
    assert out.halted is False
    names = [c.check for c in out.checks]
    assert names[0] == "kill_switch"
    assert "balance" in names and "sl_distance" in names
    assert all(c.passed for c in out.checks)


def test_precheck_halted_buy_rejected(session):
    from src.services.risk.kill_switch import KillSwitchService

    KillSwitchService(session).pause(operator_user_id=1, reason="test halt")
    session.commit()
    out = _svc(session).precheck(body=_buy(), trading_mode="testnet")
    assert out.halted is True
    assert out.verdict == "REJECT"
    ks = out.checks[0]
    assert ks.check == "kill_switch" and ks.passed is False


def test_precheck_halted_sell_reduce_only_allowed(session):
    from src.services.risk.kill_switch import KillSwitchService

    session.add(Position(
        account_id=1, trading_mode="testnet", symbol="BTCUSDT", status=PositionStatus.OPEN.value,
        side="LONG", quantity=0.02, entry_price=50_000.0, stop_loss=49_000.0,
        opened_at=datetime.now(tz=timezone.utc),
    ))
    KillSwitchService(session).pause(operator_user_id=1, reason="test halt")
    session.commit()
    out = _svc(session).precheck(
        body=_buy(side="SELL", reduce_only=True), trading_mode="testnet",
    )
    assert out.halted is True
    assert out.checks[0].check == "kill_switch"
    assert out.checks[0].passed is True  # reduce-only 放行
    assert out.verdict == "PASS"


def test_precheck_sell_without_position_rejected(session):
    out = _svc(session).precheck(
        body=_buy(side="SELL", reduce_only=True), trading_mode="testnet",
    )
    assert out.verdict == "REJECT"
    pe = next(c for c in out.checks if c.check == "position_exists")
    assert pe.passed is False


def test_precheck_buy_notional_exceeds_balance_rejected(session):
    out = _svc(session).precheck(
        body=_buy(qty=1.0),  # 1 BTC × 50000 = 50000 > 10000 可用
        trading_mode="testnet",
    )
    assert out.verdict == "REJECT"
    bal = next(c for c in out.checks if c.check == "balance")
    assert bal.passed is False
    assert "insufficient_balance" in bal.note


def test_precheck_buy_oversize_rejected(session):
    out = _svc(session).precheck(
        body=_buy(qty=0.06),  # 0.06×50000=3000 → 30% > 20% 上限
        trading_mode="testnet",
    )
    assert out.verdict == "REJECT"
    ps = next(c for c in out.checks if c.check == "position_size")
    assert ps.passed is False
