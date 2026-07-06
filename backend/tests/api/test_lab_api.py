"""/api/lab API 层测试 (handoff P5): 端点 + RBAC。"""
from __future__ import annotations

import os
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app import app
from src.controllers.dependencies import get_current_user
from src.db.session import get_db
from src.models import Base


@pytest.fixture
def engine():
    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)
    return eng


def _client(engine, role: str) -> TestClient:
    def _override():
        s = Session(engine)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="u", role=role, status="active",
    )
    return TestClient(app)


@pytest.fixture(autouse=True)
def _cleanup():
    yield
    app.dependency_overrides.clear()


def test_lab_full_flow_via_api(engine):
    trader = _client(engine, "trader")
    r = trader.post("/api/lab/candidates", json={
        "name": "SL 收紧", "description": "0.8x", "params": {"sl_mult": 0.8},
    })
    assert r.json()["success"] is True
    cand = r.json()["data"]
    assert cand["stage"] == "QUEUED"
    assert cand["promote_eligible"] is False

    r = trader.post(f"/api/lab/candidates/{cand['id']}/start")
    assert r.json()["data"]["stage"] == "SHADOW"

    # trader 不能 promote (admin+)
    r = trader.post(f"/api/lab/candidates/{cand['id']}/promote")
    assert r.json()["code"] == "400004"

    # admin promote 但门槛未达 → 业务错 (非权限)
    admin = _client(engine, "admin")
    r = admin.post(f"/api/lab/candidates/{cand['id']}/promote")
    assert r.json()["success"] is False
    assert r.json()["code"] != "400004"
    assert "门槛" in r.json()["message"]

    # 列表与历史 viewer 可见
    viewer = _client(engine, "viewer")
    assert viewer.get("/api/lab/candidates").json()["success"] is True
    assert viewer.get("/api/lab/history").json()["success"] is True
    # viewer 不能提交
    assert viewer.post("/api/lab/candidates", json={"name": "xx"}).json()["code"] == "400004"

    # terminate (依赖覆盖是全局的, 需切回 trader 身份)
    trader = _client(engine, "trader")
    r = trader.post(f"/api/lab/candidates/{cand['id']}/terminate", json={"reason": "算了"})
    assert r.json()["data"]["stage"] == "RETIRED"


def test_lab_rejects_anonymous():
    assert TestClient(app).get("/api/lab/candidates").json()["code"] == "400003"
