"""RiskStateService 单测 (webapp 架构 B2)。"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.common.enums import PositionStatus
from src.models import Base
from src.models.account import AccountSnapshot
from src.models.account_entity import RiskProfile
from src.models.event_store import EventOutbox
from src.models.position import Position
from src.models.regime import RegimeSnapshot
from src.services.events.outbox import OutboxWriter
from src.services.risk.risk_state import RiskStateService


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
        s.commit()
        yield s


def _snapshot(session, *, daily_pnl_pct=0.0, total=10_000.0):
    session.add(AccountSnapshot(
        account_id=1, trading_mode="testnet",
        snapshot_at=datetime.now(tz=timezone.utc),
        total_balance_usdt=total, available_balance_usdt=total,
        unrealized_pnl=0, daily_pnl=daily_pnl_pct * total, daily_pnl_pct=daily_pnl_pct,
    ))
    session.commit()


def test_state_ok_when_clean(session):
    _snapshot(session)
    out = RiskStateService(session).compute(trading_mode="testnet")
    assert out["state"] == "OK"
    assert out["day_loss_pct"] == 0.0
    assert out["positions_pct"] == 0.0
    assert out["regime"] is None


def test_state_warn_when_day_loss_over_half_limit(session):
    _snapshot(session, daily_pnl_pct=-0.02)  # 上限 3%, 一半 1.5%
    out = RiskStateService(session).compute(trading_mode="testnet")
    assert out["state"] == "WARN"


def test_state_halted_when_paused(session):
    from src.services.risk.kill_switch import KillSwitchService

    _snapshot(session)
    KillSwitchService(session).pause(operator_user_id=1, reason="t")
    session.commit()
    out = RiskStateService(session).compute(trading_mode="testnet")
    assert out["state"] == "HALTED"


def test_positions_pct_and_regime(session):
    _snapshot(session, total=10_000.0)
    now = datetime.now(tz=timezone.utc)
    session.add(Position(
        account_id=1, trading_mode="testnet", symbol="BTCUSDT",
        status=PositionStatus.OPEN.value, side="LONG",
        quantity=0.02, entry_price=50_000.0, stop_loss=49_000.0,
        current_price=50_000.0, opened_at=now,
    ))
    session.add(RegimeSnapshot(
        account_id=1, trading_mode="testnet", symbol="BTCUSDT", timeframe="1h",
        snapshot_at=now, regime="ranging", confidence=0.8,
    ))
    session.commit()
    out = RiskStateService(session).compute(trading_mode="testnet")
    assert out["positions_pct"] == pytest.approx(0.1)  # 1000/10000
    assert out["regime"] == "ranging"


def test_publish_writes_risk_state_event(session):
    _snapshot(session)
    RiskStateService(session, outbox=OutboxWriter()).publish(
        trading_mode="testnet", trace_id="t1",
    )
    session.commit()
    rows = [
        r for r in session.execute(select(EventOutbox)).scalars().all()
        if r.event_type == "risk.state"
    ]
    assert len(rows) == 1
    assert rows[0].payload_json["payload"]["state"] == "OK"
