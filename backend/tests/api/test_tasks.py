"""GET /api/tasks/{task_id} 集成测试 — 异步任务 HTTP 兜底层 (project.md §8)。"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app import app
from src.db.session import get_db
from src.models import Base
from src.models.task_request import TaskRequest


@pytest.fixture
def client():
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

    from types import SimpleNamespace

    from src.controllers.dependencies import require_admin

    app.dependency_overrides[require_admin] = lambda: SimpleNamespace(
        id=1, username="admin_test", role="admin", status="active",
    )

    yield TestClient(app), engine
    app.dependency_overrides.clear()


def test_get_task_returns_status_fields(client):
    cli, engine = client
    with Session(engine) as s:
        obj = TaskRequest(
            task_type="MANUAL_CLOSE_ALL", payload={"account_id": 1},
            status="SUCCESS", attempts=1, trading_mode="testnet",
        )
        s.add(obj)
        s.commit()
        task_id = obj.id

    r = cli.get(f"/api/tasks/{task_id}")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["id"] == task_id
    assert data["task_type"] == "MANUAL_CLOSE_ALL"
    assert data["status"] == "SUCCESS"
    assert data["attempts"] == 1
    assert data["trading_mode"] == "testnet"
    assert data["error_message"] is None


def test_get_task_not_found_returns_business_error(client):
    cli, _ = client
    r = cli.get("/api/tasks/999999")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body["code"] == "400005"


def test_get_task_rejects_anonymous():
    """不 override require_admin 时, 匿名访问 → 业务异常 AUTH_ERROR (HTTP 200 + 400003)。"""
    cli = TestClient(app)
    r = cli.get("/api/tasks/1")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body["code"] == "400003"
