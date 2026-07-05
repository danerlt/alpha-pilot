"""GET /api/decisions/{id} API 层测试。"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app import app
from src.db.session import get_db
from src.models import Base
from src.models.decision import AIDecision


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


def _seed_decision(engine) -> int:
    with Session(engine) as s:
        d = AIDecision(
            account_id=1, trading_mode="testnet", symbol="BTCUSDT",
            timeframe="1h", decided_at=datetime.now(tz=timezone.utc),
            action="HOLD", confidence=0.5, is_fallback=False,
        )
        s.add(d)
        s.commit()
        return d.id


def test_decision_detail_returns_full_payload(authed_client):
    cli, engine = authed_client
    decision_id = _seed_decision(engine)
    r = cli.get(f"/api/decisions/{decision_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["id"] == decision_id
    assert data["action"] == "HOLD"
    assert "features" in data
    assert "reviews" in data
    assert "guard_events" in data
    assert "orders" in data


def test_decision_detail_not_found(authed_client):
    cli, _ = authed_client
    r = cli.get("/api/decisions/999999")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body["code"] == "400005"


def test_decision_detail_rejects_anonymous():
    cli = TestClient(app)
    r = cli.get("/api/decisions/1")
    assert r.status_code == 200
    assert r.json()["code"] == "400003"
