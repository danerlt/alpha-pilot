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


# ── place_order (handoff P2 Task 6) ─────────────────────────────────────


def _place(session, body, **kw):
    defaults = dict(trading_mode="testnet", operator_user_id=1)
    defaults.update(kw)
    return _svc(session).place_order(body=body, **defaults)


def test_place_order_buy_writes_order_and_position(session):
    out = _place(session, _buy(client_order_id="c1"))
    assert out["order_id"] is not None
    assert out["position_id"] is not None
    assert out["status"] in {"FILLED", "filled"}
    from sqlalchemy import select as _select

    from src.models.order import Order

    order = session.execute(_select(Order)).scalars().one()
    assert order.ai_decision_id is None
    assert order.side == "BUY"
    # 审计行
    from src.models.audit_log import AuditLog

    logs = session.execute(_select(AuditLog)).scalars().all()
    assert any(log.action == "manual_order" for log in logs)


def test_place_order_idempotent_same_client_order_id(session):
    out1 = _place(session, _buy(client_order_id="dup1"))
    out2 = _place(session, _buy(client_order_id="dup1"))
    assert out1["order_id"] == out2["order_id"]
    from sqlalchemy import select as _select

    from src.models.order import Order

    assert len(session.execute(_select(Order)).scalars().all()) == 1


def test_place_order_rejected_writes_nothing(session):
    from sqlalchemy import select as _select

    from src.common.exception.errors import RiskRejectedException
    from src.models.order import Order

    with pytest.raises(RiskRejectedException):
        _place(session, _buy(qty=0.06, client_order_id="c2"))  # oversize 30%
    assert session.execute(_select(Order)).scalars().all() == []


def test_place_order_limit_not_supported(session):
    from src.common.exception.errors import ServiceException

    with pytest.raises(ServiceException):
        _place(session, _buy(type="LIMIT", price=49_000.0, client_order_id="c3"))


def test_place_order_halted_buy_rejected(session):
    from src.common.exception.errors import RiskRejectedException
    from src.services.risk.kill_switch import KillSwitchService

    KillSwitchService(session).pause(operator_user_id=1, reason="halt")
    session.commit()
    with pytest.raises(RiskRejectedException):
        _place(session, _buy(client_order_id="c4"))


def test_place_order_sell_closes_position(session):
    session.add(Position(
        account_id=1, trading_mode="testnet", symbol="BTCUSDT",
        status=PositionStatus.OPEN.value, side="LONG",
        quantity=0.02, entry_price=49_000.0, stop_loss=48_000.0,
        opened_at=datetime.now(tz=timezone.utc),
    ))
    session.commit()
    out = _place(
        session, _buy(side="SELL", reduce_only=True, client_order_id="c5"),
    )
    assert out["trade_id"] is not None
    from sqlalchemy import select as _select

    from src.models.trade import Trade

    trade = session.execute(_select(Trade)).scalars().one()
    assert trade.exit_reason == "manual"
    pos = session.execute(_select(Position)).scalars().one()
    assert pos.status == PositionStatus.CLOSED.value


# ── update_sltp (handoff P2 Task 7) ─────────────────────────────────────


def _open_position(session, **kw) -> Position:
    defaults = dict(
        account_id=1, trading_mode="testnet", symbol="BTCUSDT",
        status=PositionStatus.OPEN.value, side="LONG",
        quantity=0.02, entry_price=49_000.0, stop_loss=48_000.0,
        opened_at=datetime.now(tz=timezone.utc),
    )
    defaults.update(kw)
    pos = Position(**defaults)
    session.add(pos)
    session.commit()
    return pos


def test_update_sltp_success_and_audited(session):
    from sqlalchemy import select as _select

    from src.models.audit_log import AuditLog
    from src.schemas.manual_order import SltpUpdate

    pos = _open_position(session)
    out = _svc(session).update_sltp(
        position_id=pos.id, body=SltpUpdate(stop_loss=49_500.0, take_profit=51_000.0),
        trading_mode="testnet", operator_user_id=1,
    )
    assert out["stop_loss"] == 49_500.0
    assert out["take_profit"] == 51_000.0
    session.expire_all()
    assert float(session.get(Position, pos.id).stop_loss) == 49_500.0
    logs = session.execute(_select(AuditLog)).scalars().all()
    assert any(log.action == "manual_sltp_update" for log in logs)


def test_update_sltp_sl_above_price_rejected(session):
    from src.common.exception.errors import RiskRejectedException
    from src.schemas.manual_order import SltpUpdate

    pos = _open_position(session)
    with pytest.raises(RiskRejectedException):
        _svc(session).update_sltp(
            position_id=pos.id, body=SltpUpdate(stop_loss=50_500.0),  # 现价 50000
            trading_mode="testnet", operator_user_id=1,
        )


def test_update_sltp_tp_below_price_rejected(session):
    from src.common.exception.errors import RiskRejectedException
    from src.schemas.manual_order import SltpUpdate

    pos = _open_position(session)
    with pytest.raises(RiskRejectedException):
        _svc(session).update_sltp(
            position_id=pos.id, body=SltpUpdate(take_profit=49_000.0),
            trading_mode="testnet", operator_user_id=1,
        )


def test_update_sltp_sl_distance_out_of_atr_range_rejected(session):
    from src.common.exception.errors import RiskRejectedException
    from src.models.indicator import IndicatorSnapshot
    from src.schemas.manual_order import SltpUpdate

    session.add(IndicatorSnapshot(
        account_id=1, trading_mode="testnet", symbol="BTCUSDT", timeframe="1h",
        snapshot_at=datetime.now(tz=timezone.utc), atr=200.0,
    ))
    session.commit()
    pos = _open_position(session)
    with pytest.raises(RiskRejectedException):
        # 距离 5000 > 5×200 上限
        _svc(session).update_sltp(
            position_id=pos.id, body=SltpUpdate(stop_loss=45_000.0),
            trading_mode="testnet", operator_user_id=1,
        )


def test_update_sltp_missing_fields_rejected(session):
    from src.common.exception.errors import ParamsException
    from src.schemas.manual_order import SltpUpdate

    pos = _open_position(session)
    with pytest.raises(ParamsException):
        _svc(session).update_sltp(
            position_id=pos.id, body=SltpUpdate(),
            trading_mode="testnet", operator_user_id=1,
        )


def test_update_sltp_closed_position_not_found(session):
    from src.common.exception.errors import DBException
    from src.schemas.manual_order import SltpUpdate

    pos = _open_position(session, status=PositionStatus.CLOSED.value)
    with pytest.raises(DBException):
        _svc(session).update_sltp(
            position_id=pos.id, body=SltpUpdate(stop_loss=49_500.0),
            trading_mode="testnet", operator_user_id=1,
        )
