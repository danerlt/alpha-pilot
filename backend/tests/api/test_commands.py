"""Commands router 集成测试 (FastAPI TestClient)。"""
from __future__ import annotations

import os

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.db.engines import get_session_factory
from src.db.session import get_db
from src.common.enums import PositionStatus
from src.models import Base, Position, RiskEvent
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@pytest.fixture
def client():
    # SQLite in-memory + StaticPool 让多 session 共享同一个连接 (否则 :memory: 各自隔离)
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"),
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
    from src.controllers.dependencies import require_admin
    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(
        id=1, username="admin_test", role="admin", status="active",
    )

    # 替换 _adapter() 用 stub
    from src.controllers.api.v1.risk import commands as commands_module

    class _StubAdapter:
        @property
        def trading_mode(self): return "testnet"
        def get_ticker(self, s):
            from src.core.exchange.types import Ticker
            return Ticker(symbol=s, price=50_000.0)
        def get_klines(self, s, t, **kw): return []
        def submit_order(self, r):
            from src.core.exchange.types import OrderResult
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
    assert r.json()["data"] == {"state": "active"}


def test_pause_then_resume(client):
    cli, _ = client
    r = cli.post("/api/commands/pause", json={"reason": "test"})
    assert r.status_code == 200
    assert r.json()["data"]["state"] == "paused"
    r = cli.post("/api/commands/resume", json={"reason": "ok"})
    assert r.json()["data"]["state"] == "active"


def test_close_all_requires_confirmation(client):
    cli, _ = client
    r = cli.post("/api/commands/close-all", json={
        "confirmation": "wrong",
        "reason": "test",
    })
    assert r.status_code == 200; assert r.json()["success"] is False; assert r.json()["code"] == "400001"


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
    assert len(r.json()["data"]["closed_position_ids"]) == 1


def test_close_position_not_found(client):
    cli, _ = client
    r = cli.post("/api/commands/close-position/9999", json={"reason": "test"})
    assert r.status_code == 200; assert r.json()["success"] is False; assert r.json()["code"] == "400005"


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
    assert r.json()["data"]["resolved"] is True


def test_resolve_breaker_emits_manual_override_event(client):
    """Critical fix (post Plan5 minor): commands router 必须传 outbox 给
    ManualOpsService, 否则 manual.override 事件丢失."""
    from sqlalchemy import select
    from src.models.event_store import EventOutbox

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

    cli.post(f"/api/commands/resolve-breaker/{eid}", json={"reason": "manual ok"})

    with Session(engine) as s:
        rows = s.execute(
            select(EventOutbox).where(EventOutbox.event_type == "manual.override")
        ).scalars().all()
    assert len(rows) == 1
    payload = rows[0].payload_json["payload"]
    assert payload["operator_user_id"] == 1
    assert "circuit_breaker" in payload["target"] or str(eid) in payload["target"]


def test_close_all_emits_manual_override_event(client):
    """同 above: close-all 也必须发 manual.override (一个或多个)."""
    from sqlalchemy import select
    from src.models.event_store import EventOutbox

    cli, engine = client
    with Session(engine) as s:
        s.add(Position(
            account_id=1, trading_mode="testnet",
            symbol="BTCUSDT", status=PositionStatus.OPEN.value, side="LONG",
            quantity=0.01, entry_price=50_000.0, stop_loss=49_000.0,
            opened_at=datetime.now(tz=timezone.utc),
        ))
        s.commit()

    cli.post("/api/commands/close-all", json={
        "confirmation": "CLOSE ALL", "reason": "emergency",
    })

    with Session(engine) as s:
        rows = s.execute(
            select(EventOutbox).where(EventOutbox.event_type == "manual.override")
        ).scalars().all()
    assert len(rows) >= 1
    assert rows[0].payload_json["payload"]["operator_user_id"] == 1
