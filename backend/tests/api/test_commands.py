"""Commands router 集成测试 (FastAPI TestClient)。"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.app.app import app
from src.shared.db import get_db, get_session_factory
from src.shared.enums import PositionStatus
from src.shared.models import Base, Position, RiskEvent
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@pytest.fixture
def client():
    # SQLite in-memory + StaticPool 让多 session 共享同一个连接 (否则 :memory: 各自隔离)
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def _override():
        s = Session(engine)
        try:
            yield s
        finally:
            s.close()
    app.dependency_overrides[get_db] = _override

    # 鉴权 mock: 测试中绕过 JWT 解码, 注入 admin user.
    from types import SimpleNamespace
    from src.app.dependencies import require_admin
    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(
        id=1, username="admin_test", role="admin", status="active",
    )

    # 替换 _adapter() 用 stub
    from src.app.routers import commands as commands_module

    class _StubAdapter:
        @property
        def trading_mode(self): return "testnet"
        def get_ticker(self, s):
            from src.execution.exchange.types import Ticker
            return Ticker(symbol=s, price=50_000.0)
        def get_klines(self, s, t, **kw): return []
        def submit_order(self, r):
            from src.execution.exchange.types import OrderResult
            return OrderResult(
                exchange_order_id="EX", symbol=r.symbol, side=r.side,
                order_type=r.order_type, status="FILLED",
                requested_quantity=r.quantity, filled_quantity=r.quantity,
                avg_fill_price=50_000.0, client_order_id=r.client_order_id,
            )
        def get_order(self, s, oid): raise NotImplementedError
        def cancel_order(self, s, oid): raise NotImplementedError
        def get_balance(self, asset): return 10_000.0

    commands_module._adapter = lambda: _StubAdapter()

    yield TestClient(app), engine
    app.dependency_overrides.clear()


def test_kill_switch_default_state(client):
    cli, _ = client
    r = cli.get("/api/commands/kill-switch")
    assert r.status_code == 200
    assert r.json() == {"state": "active"}


def test_pause_then_resume(client):
    cli, _ = client
    r = cli.post("/api/commands/pause", json={"reason": "test"})
    assert r.status_code == 200
    assert r.json()["state"] == "paused"
    r = cli.post("/api/commands/resume", json={"reason": "ok"})
    assert r.json()["state"] == "active"


def test_close_all_requires_confirmation(client):
    cli, _ = client
    r = cli.post("/api/commands/close-all", json={
        "confirmation": "wrong",
        "reason": "test",
    })
    assert r.status_code == 400


def test_close_all_returns_closed_ids(client):
    cli, engine = client
    with Session(engine) as s:
        s.add(Position(
            account_id=1, trading_mode="testnet",
            symbol="BTCUSDT", status=PositionStatus.OPEN.value, side="LONG",
            quantity=0.01, entry_price=50_000.0, stop_loss=49_000.0,
            opened_at=datetime.now(tz=timezone.utc),
        ))
        s.commit()

    r = cli.post("/api/commands/close-all", json={
        "confirmation": "CLOSE ALL",
        "reason": "emergency",
    })
    assert r.status_code == 200
    assert len(r.json()["closed_position_ids"]) == 1


def test_close_position_not_found(client):
    cli, _ = client
    r = cli.post("/api/commands/close-position/9999", json={"reason": "test"})
    assert r.status_code == 404


def test_resolve_breaker(client):
    cli, engine = client
    with Session(engine) as s:
        ev = RiskEvent(
            account_id=1, trading_mode="testnet",
            event_type="CIRCUIT_BREAKER_TRIGGERED",
            triggered_at=datetime.now(tz=timezone.utc),
            description="t", resolved=False,
        )
        s.add(ev)
        s.commit()
        eid = ev.id

    r = cli.post(f"/api/commands/resolve-breaker/{eid}", json={"reason": "manual ok"})
    assert r.status_code == 200
    assert r.json()["resolved"] is True
