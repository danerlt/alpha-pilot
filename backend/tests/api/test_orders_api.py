"""/api/orders API 层测试 (handoff P2 §3.2)。"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app import app
from src.controllers.dependencies import get_adapter, get_current_user
from src.db.session import get_db
from src.models import Base
from src.models.account import AccountSnapshot
from src.models.account_entity import RiskProfile
from tests.unit.execution.test_manual_trade import _StubAdapter


@pytest.fixture
def engine():
    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)
    with Session(eng) as s:
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
    return eng


@pytest.fixture
def admin_client(engine):
    def _override():
        s = Session(engine)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    from types import SimpleNamespace

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="admin", role="admin", status="active",
    )
    app.dependency_overrides[get_adapter] = lambda: _StubAdapter()
    yield TestClient(app), engine
    app.dependency_overrides.clear()


_BUY = {
    "symbol": "BTCUSDT", "side": "BUY", "type": "MARKET",
    "qty": 0.02, "sl": 49_900.0, "tp": 50_500.0, "reduce_only": False,
}


def test_precheck_returns_itemized_checks(admin_client):
    cli, _ = admin_client
    r = cli.post("/api/orders/precheck", json=_BUY)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["verdict"] == "PASS"
    assert data["halted"] is False
    assert data["checks"][0]["check"] == "kill_switch"
    assert all(set(c) == {"check", "pass", "note"} for c in data["checks"])


def test_precheck_requires_admin(engine):
    def _override():
        s = Session(engine)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    from types import SimpleNamespace

    from src.controllers.dependencies import get_current_user as dep_user
    app.dependency_overrides[dep_user] = lambda: SimpleNamespace(
        id=2, username="u", role="user", status="active",
    )
    try:
        cli = TestClient(app)
        r = cli.post("/api/orders/precheck", json=_BUY)
        assert r.status_code == 200
        assert r.json()["code"] == "400004"  # FORBIDDEN
    finally:
        app.dependency_overrides.clear()


def test_precheck_rejects_anonymous():
    cli = TestClient(app)
    r = cli.post("/api/orders/precheck", json=_BUY)
    assert r.status_code == 200
    assert r.json()["code"] == "400003"
