"""KillSwitchService 单测。"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.models import AuditLog, Base, RiskEvent
from src.services.risk.kill_switch import (
    ACTIVE,
    PAUSED,
    KillSwitchService,
)


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_default_state_is_active(session):
    svc = KillSwitchService(session)
    assert svc.state() == ACTIVE
    assert svc.is_paused() is False


def test_pause_then_resume(session):
    svc = KillSwitchService(session)
    svc.pause(operator_user_id=1, reason="maintenance")
    assert svc.is_paused() is True
    svc.resume(operator_user_id=1, reason="ok")
    assert svc.state() == ACTIVE


def test_pause_writes_audit_log(session):
    svc = KillSwitchService(session)
    svc.pause(operator_user_id=42, reason="emergency")
    rows = session.execute(select(AuditLog)).scalars().all()
    assert len(rows) == 1
    assert rows[0].action == "kill_switch_pause"
    assert rows[0].user_id == 42
    assert rows[0].after_json["state"] == PAUSED


def test_resume_writes_audit_log(session):
    svc = KillSwitchService(session)
    svc.pause(operator_user_id=1, reason="x")
    svc.resume(operator_user_id=2, reason="y")
    rows = session.execute(
        select(AuditLog).where(AuditLog.action == "kill_switch_resume")
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].user_id == 2


# ---------------------------------------------------------------------------
# 熔断查询 + 统一阻塞接口 (Plan5 codereview I2)
# ---------------------------------------------------------------------------

def _add_circuit_breaker(
    session: Session, *, account_id: int = 1, trading_mode: str = "testnet",
    resolved: bool = False, triggered_at: datetime | None = None,
) -> RiskEvent:
    row = RiskEvent(
        account_id=account_id, trading_mode=trading_mode,
        event_type="CIRCUIT_BREAKER_TRIGGERED",
        triggered_at=triggered_at or datetime.now(tz=timezone.utc),
        description="test breaker",
        resolved=resolved,
    )
    session.add(row)
    session.flush()
    return row


def test_has_unresolved_circuit_breaker_default_false(session):
    svc = KillSwitchService(session)
    assert svc.has_unresolved_circuit_breaker(
        account_id=1, trading_mode="testnet",
    ) is False


def test_has_unresolved_circuit_breaker_true_when_today_unresolved(session):
    _add_circuit_breaker(session)
    svc = KillSwitchService(session)
    assert svc.has_unresolved_circuit_breaker(
        account_id=1, trading_mode="testnet",
    ) is True


def test_resolved_circuit_breaker_does_not_block(session):
    _add_circuit_breaker(session, resolved=True)
    svc = KillSwitchService(session)
    assert svc.has_unresolved_circuit_breaker(
        account_id=1, trading_mode="testnet",
    ) is False


def test_yesterday_circuit_breaker_does_not_block_today(session):
    yesterday = datetime.now(tz=timezone.utc) - timedelta(days=1, hours=1)
    _add_circuit_breaker(session, triggered_at=yesterday)
    svc = KillSwitchService(session)
    assert svc.has_unresolved_circuit_breaker(
        account_id=1, trading_mode="testnet",
    ) is False


def test_other_account_circuit_breaker_does_not_leak(session):
    _add_circuit_breaker(session, account_id=2)
    svc = KillSwitchService(session)
    assert svc.has_unresolved_circuit_breaker(
        account_id=1, trading_mode="testnet",
    ) is False


def test_other_trading_mode_circuit_breaker_isolated(session):
    _add_circuit_breaker(session, trading_mode="mainnet")
    svc = KillSwitchService(session)
    assert svc.has_unresolved_circuit_breaker(
        account_id=1, trading_mode="testnet",
    ) is False


def test_should_block_when_paused(session):
    svc = KillSwitchService(session)
    svc.pause(operator_user_id=1, reason="x")
    assert svc.should_block_new_trades(
        account_id=1, trading_mode="testnet",
    ) is True


def test_should_block_when_circuit_breaker(session):
    _add_circuit_breaker(session)
    svc = KillSwitchService(session)
    # 没人工 pause, 但今天有未 resolved 熔断 → 一样阻塞
    assert svc.is_paused() is False
    assert svc.should_block_new_trades(
        account_id=1, trading_mode="testnet",
    ) is True


def test_should_not_block_when_clean(session):
    svc = KillSwitchService(session)
    assert svc.should_block_new_trades(
        account_id=1, trading_mode="testnet",
    ) is False
