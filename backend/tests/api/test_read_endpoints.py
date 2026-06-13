"""只读业务端点 API 层测试 (TEST-2 补强)。

覆盖 6 个 GET 端点: positions / trades / account / decisions / risk-events / reports。
统一验证: 鉴权后返回 envelope success / 匿名被拒 (AUTH_ERROR)。
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app import app
from src.common.enums import PositionStatus
from src.db.session import get_db
from src.models import Base, Position, Trade

READ_ENDPOINTS = [
    "/api/positions",
    "/api/trades",
    "/api/account",
    "/api/decisions",
    "/api/risk-events",
    "/api/reports",
]


@pytest.fixture
def engine():
    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def authed_client(engine):
    def _override():
        s = Session(engine)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override

    from types import SimpleNamespace

    from src.controllers.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="u", role="user", status="active",
    )
    yield TestClient(app), engine
    app.dependency_overrides.clear()


@pytest.mark.parametrize("path", READ_ENDPOINTS)
def test_read_endpoint_authed_returns_success_envelope(authed_client, path):
    cli, _ = authed_client
    r = cli.get(path)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["code"] == "0"
    assert "data" in body


@pytest.mark.parametrize("path", READ_ENDPOINTS)
def test_read_endpoint_rejects_anonymous(path):
    """无鉴权 override 时, 匿名访问 → AUTH_ERROR (HTTP 200 + 400003)。"""
    cli = TestClient(app)
    r = cli.get(path)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body["code"] == "400003"


def test_positions_returns_open_rows(authed_client):
    cli, engine = authed_client
    with Session(engine) as s:
        s.add(Position(
            account_id=1, trading_mode="testnet", symbol="BTCUSDT",
            status=PositionStatus.OPEN.value, side="LONG",
            quantity=0.01, entry_price=50_000.0, stop_loss=49_000.0,
            opened_at=datetime.now(tz=timezone.utc),
        ))
        s.commit()
    r = cli.get("/api/positions")
    data = r.json()["data"]
    assert len(data) == 1
    assert data[0]["symbol"] == "BTCUSDT"


def test_trades_returns_closed_rows(authed_client):
    cli, engine = authed_client
    now = datetime.now(tz=timezone.utc)
    with Session(engine) as s:
        s.add(Trade(
            account_id=1, trading_mode="testnet", position_id=1, symbol="ETHUSDT",
            side="LONG", quantity=0.1, entry_price=3000.0, exit_price=3100.0,
            pnl=10.0, pnl_pct=0.033, exit_reason="take_profit",
            opened_at=now, closed_at=now, holding_seconds=3600,
        ))
        s.commit()
    r = cli.get("/api/trades")
    data = r.json()["data"]
    assert len(data) == 1
    assert data[0]["symbol"] == "ETHUSDT"


def test_account_empty_returns_message(authed_client):
    cli, _ = authed_client
    r = cli.get("/api/account")
    body = r.json()
    assert body["success"] is True
    # 无快照时返回 message 字段
    assert body["data"].get("message")
