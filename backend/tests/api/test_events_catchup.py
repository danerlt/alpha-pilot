"""GET /api/events/catchup 测试。"""
from __future__ import annotations

import os

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app import app
from src.controllers.dependencies import get_current_user
from src.shared.db import get_db
from src.models import Base, EventOutbox


@pytest.fixture
def client():
    from types import SimpleNamespace

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
    # 鉴权 mock: 注入 stub user, 测试不验 JWT
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="user_test", role="user", status="active",
    )
    yield TestClient(app), engine
    app.dependency_overrides.clear()


def test_catchup_requires_authentication():
    """缺 token / 未注入鉴权 override 时, /catchup 必须 401."""
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
    try:
        cli = TestClient(app)
        r = cli.get("/api/events/catchup")
        assert r.status_code == 401
    finally:
        app.dependency_overrides.clear()


def _seed(session, n: int = 5):
    """种子 n 条已 published 的 outbox 行, event_id 用 UUIDv7 时间序。"""
    from src.services.events.ids import new_event_id
    import time
    rows = []
    for i in range(n):
        eid = new_event_id()
        rows.append(EventOutbox(
            aggregate_type="position", aggregate_id=i + 1,
            event_type=f"position.opened",
            event_id=eid,
            payload_json={"event_id": eid, "test_index": i},
            published_at=datetime.now(tz=timezone.utc),
        ))
        time.sleep(0.001)  # ensure UUIDv7 time order
    session.add_all(rows)
    session.commit()
    return rows


def test_catchup_returns_all_published_events(client):
    cli, engine = client
    with Session(engine) as s:
        rows = _seed(s, n=3)
    r = cli.get("/api/events/catchup")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 3
    assert all(e["event_type"] == "position.opened" for e in body["events"])


def test_catchup_filters_by_since(client):
    cli, engine = client
    with Session(engine) as s:
        rows = _seed(s, n=5)
        third_event_id = rows[2].event_id
    r = cli.get(f"/api/events/catchup?since={third_event_id}")
    body = r.json()
    # since=第 3 个 event_id; 应返回第 4、5 共 2 条
    assert body["count"] == 2
    returned_ids = [e["event_id"] for e in body["events"]]
    assert third_event_id not in returned_ids


def test_catchup_respects_limit(client):
    cli, engine = client
    with Session(engine) as s:
        _seed(s, n=10)
    r = cli.get("/api/events/catchup?limit=3")
    body = r.json()
    assert body["count"] == 3


def test_catchup_excludes_unpublished(client):
    cli, engine = client
    with Session(engine) as s:
        # 一条 published, 一条 published_at=None
        from src.services.events.ids import new_event_id
        s.add(EventOutbox(
            aggregate_type="x", aggregate_id=1, event_type="x.published",
            event_id=new_event_id(),
            payload_json={"published": True},
            published_at=datetime.now(tz=timezone.utc),
        ))
        s.add(EventOutbox(
            aggregate_type="x", aggregate_id=2, event_type="x.pending",
            event_id=new_event_id(),
            payload_json={"published": False},
            published_at=None,
        ))
        s.commit()
    r = cli.get("/api/events/catchup")
    body = r.json()
    assert body["count"] == 1
    assert body["events"][0]["event_type"] == "x.published"
