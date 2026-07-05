"""/api/agent API 层测试 (handoff P3)。"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app import app
from src.controllers.dependencies import get_adapter, get_current_user, get_llm_client
from src.core.llm.client import LLMResult
from src.db.session import get_db
from src.models import Base
from src.models.agent_pending_action import AgentPendingAction
from tests.unit.execution.test_manual_trade import _StubAdapter


class _SeqLLM:
    provider = "mock"

    def __init__(self, responses):
        self._responses = list(responses)

    def complete(self, *, system, user, max_tokens=1024, timeout_s=30):
        return LLMResult(raw_text=self._responses.pop(0), provider="mock")


@pytest.fixture
def engine():
    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)
    return eng


def _client(engine, *, role="user", llm_responses=None):
    def _override():
        s = Session(engine)
        try:
            yield s
        finally:
            s.close()

    from types import SimpleNamespace

    app.dependency_overrides[get_db] = _override
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="u", role=role, status="active",
    )
    app.dependency_overrides[get_adapter] = lambda: _StubAdapter()
    app.dependency_overrides[get_llm_client] = lambda: _SeqLLM(
        llm_responses or [json.dumps({"final": "OK"})]
    )
    return TestClient(app)


@pytest.fixture(autouse=True)
def _cleanup():
    yield
    app.dependency_overrides.clear()


def test_chat_sse_stream_contains_delta_and_done(engine):
    cli = _client(engine, llm_responses=[json.dumps({"final": "现在一切正常。"})])
    with cli.stream("POST", "/api/agent/chat", json={"message": "风控现在什么状态?"}) as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        body = "".join(r.iter_text())
    assert "event: delta" in body
    assert "event: done" in body
    assert "invocation_id" in body


def test_chat_with_tool_emits_tool_call_events(engine):
    cli = _client(engine, llm_responses=[
        json.dumps({"tool": "get_risk_state", "args": {}}),
        json.dumps({"final": "风控状态 OK。"}),
    ])
    with cli.stream("POST", "/api/agent/chat", json={"message": "风险敞口?"}) as r:
        body = "".join(r.iter_text())
    assert "event: tool_call" in body
    assert "get_risk_state" in body


def test_history_returns_items(engine):
    cli = _client(engine, llm_responses=[json.dumps({"final": "答案"})])
    with cli.stream("POST", "/api/agent/chat", json={"message": "问题"}) as r:
        "".join(r.iter_text())
    r2 = cli.get("/api/agent/history")
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert len(data) == 1
    assert data[0]["message"] == "问题"
    assert data[0]["answer"] == "答案"


def test_confirm_requires_admin(engine):
    with Session(engine) as s:
        row = AgentPendingAction(
            action_type="config_change",
            payload_json={"key": "risk.max_daily_loss_pct", "value": 0.02, "reason": "t"},
            status="PENDING", proposed_at=datetime.now(tz=timezone.utc),
        )
        s.add(row)
        s.commit()
        action_id = row.id
    cli = _client(engine, role="user")
    r = cli.post(f"/api/agent/actions/{action_id}/confirm")
    assert r.json()["code"] == "400004"  # FORBIDDEN


def test_chat_rejects_anonymous():
    cli = TestClient(app)
    r = cli.post("/api/agent/chat", json={"message": "hi"})
    assert r.json()["code"] == "400003"
