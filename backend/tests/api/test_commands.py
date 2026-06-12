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

    # close-all 走异步入队: 注入绑定测试 engine 的 dispatcher + MagicMock redis
    import contextlib
    from unittest.mock import MagicMock
    from src.services.task_dispatcher import TaskDispatcher

    @contextlib.contextmanager
    def _db_factory():
        s = Session(engine)
        try:
            yield s
        finally:
            s.close()

    fake_redis = MagicMock()
    test_dispatcher = TaskDispatcher(db_factory=_db_factory, redis_client=fake_redis, queue_key="t:q")
    _orig_get_dispatcher = commands_module.get_task_dispatcher
    commands_module.get_task_dispatcher = lambda: test_dispatcher

    yield TestClient(app), engine
    commands_module.get_task_dispatcher = _orig_get_dispatcher
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


def test_close_all_enqueues_task_and_returns_task_id(client):
    """close-all 切异步: 立即返回 task_id + queued, 写 PENDING 行并 LPUSH (spec §4.9.1)。"""
    from src.controllers.api.v1.risk import commands as commands_module
    from src.models.task_request import TaskRequest

    cli, engine = client
    r = cli.post("/api/commands/close-all", json={
        "confirmation": "CLOSE ALL",
        "reason": "emergency",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["status"] == "queued"
    task_id = data["task_id"]

    with Session(engine) as s:
        obj = s.get(TaskRequest, task_id)
        assert obj is not None
        assert obj.status == "PENDING"
        assert obj.task_type == "MANUAL_CLOSE_ALL"
        assert obj.payload["operator_user_id"] == 1
        assert obj.payload["reason"] == "emergency"

    fake_redis = commands_module.get_task_dispatcher()._redis
    assert fake_redis.lpush.call_count == 1


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


def test_close_all_async_chain_emits_events(client, monkeypatch):
    """close-all 全链路: 入队 → dispatcher 执行 → manual.override + task.status_changed 事件。"""
    from sqlalchemy import select
    from src.controllers.api.v1.risk import commands as commands_module
    from src.models.event_store import EventOutbox
    from src.models.task_request import TaskRequest

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
        "confirmation": "CLOSE ALL", "reason": "emergency",
    })
    task_id = r.json()["data"]["task_id"]

    # 模拟 scheduler 消费: handler 内部 import get_adapter, monkeypatch 指到 stub
    import src.controllers.dependencies as deps_module
    monkeypatch.setattr(deps_module, "get_adapter", commands_module._adapter)
    dispatcher = commands_module.get_task_dispatcher()
    dispatcher._handle_one(task_id)

    with Session(engine) as s:
        obj = s.get(TaskRequest, task_id)
        assert obj.status == "SUCCESS"
        override_rows = s.execute(
            select(EventOutbox).where(EventOutbox.event_type == "manual.override")
        ).scalars().all()
        status_rows = s.execute(
            select(EventOutbox).where(EventOutbox.event_type == "task.status_changed")
        ).scalars().all()
    assert len(override_rows) >= 1
    assert override_rows[0].payload_json["payload"]["operator_user_id"] == 1
    assert len(status_rows) == 1
    assert status_rows[0].payload_json["payload"]["status"] == "SUCCESS"
