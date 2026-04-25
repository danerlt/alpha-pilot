"""KillSwitchService 单测。"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.control.kill_switch.service import (
    ACTIVE,
    KillSwitchService,
    PAUSED,
)
from src.shared.models import AuditLog, Base


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
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
