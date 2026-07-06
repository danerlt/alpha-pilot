"""/api/strategies 受限策略集测试 (浏览器验收修复 #3b)。"""
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


def _client(engine, role="admin"):
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


def test_list_and_toggle_roundtrip(engine):
    cli = _client(engine)
    rows = cli.get("/api/strategies").json()["data"]
    assert {r["id"] for r in rows} >= {"ai_trend", "ai_breakout", "ai_observation"}
    assert all(r["enabled"] for r in rows)  # 默认全启用
    assert {"id", "name", "enabled", "regimes", "desc"} <= set(rows[0])  # 前端 StrategyCard 同构

    r = cli.patch("/api/strategies/ai_trend", json={"enabled": False})
    assert r.json()["data"]["ok"] is True
    rows = cli.get("/api/strategies").json()["data"]
    assert next(x for x in rows if x["id"] == "ai_trend")["enabled"] is False


def test_toggle_unknown_mode_rejected(engine):
    cli = _client(engine)
    assert cli.patch("/api/strategies/hacker", json={"enabled": False}).json()["code"] == "400001"


def test_toggle_requires_engine_permission(engine):
    viewer = _client(engine, role="viewer")
    assert viewer.patch("/api/strategies/ai_trend", json={"enabled": False}).json()["code"] == "400004"
    # viewer 可读
    assert viewer.get("/api/strategies").json()["success"] is True
