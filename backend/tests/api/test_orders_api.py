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


def test_precheck_requires_trade_permission(engine):
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
        id=2, username="u", role="viewer", status="active",
    )
    try:
        cli = TestClient(app)
        # P4 RBAC: viewer 无 trade.manual_order → 403; user(→trader) 已放行
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


def test_place_order_buy_full_chain(admin_client):
    cli, engine = admin_client
    r = cli.post("/api/orders", json={**_BUY, "client_order_id": "api-c1"})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["order_id"] is not None
    assert data["position_id"] is not None
    # 幂等重放
    r2 = cli.post("/api/orders", json={**_BUY, "client_order_id": "api-c1"})
    assert r2.json()["data"]["order_id"] == data["order_id"]


def test_place_order_rejected_returns_risk_code(admin_client):
    cli, _ = admin_client
    r = cli.post("/api/orders", json={**_BUY, "qty": 0.06, "client_order_id": "api-c2"})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body["code"] == "600002"  # RISK_REJECTED


def test_patch_sltp_full_chain(admin_client):
    from datetime import datetime, timezone

    from src.common.enums import PositionStatus
    from src.models.position import Position

    cli, engine = admin_client
    with Session(engine) as s:
        pos = Position(
            account_id=1, trading_mode="testnet", symbol="BTCUSDT",
            status=PositionStatus.OPEN.value, side="LONG",
            quantity=0.02, entry_price=49_000.0, stop_loss=48_000.0,
            opened_at=datetime.now(tz=timezone.utc),
        )
        s.add(pos)
        s.commit()
        pos_id = pos.id
    r = cli.patch(f"/api/positions/{pos_id}/sltp", json={"stop_loss": 49_500.0})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["stop_loss"] == 49_500.0

    # 非法方向 → 600002
    r2 = cli.patch(f"/api/positions/{pos_id}/sltp", json={"stop_loss": 50_500.0})
    assert r2.json()["code"] == "600002"
