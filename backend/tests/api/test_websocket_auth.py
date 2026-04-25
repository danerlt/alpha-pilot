"""WebSocket 鉴权 + catchup 测试 (Critical fix C4)。"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.app.app import app
from src.shared.config import get_base_settings
from src.shared.db import get_db, get_session_factory
from src.shared.models import Base, EventOutbox


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng


@pytest.fixture
def client(engine, monkeypatch):
    """注入测试 SessionLocal 让 get_session_factory 返回内存 engine 的 session."""
    from sqlalchemy.orm import sessionmaker

    def _override_db():
        s = Session(engine)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override_db

    # 让 websocket._replay_since 用同一个 in-memory engine
    Local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    monkeypatch.setattr("src.app.websocket.get_session_factory", lambda: Local)

    yield TestClient(app)
    app.dependency_overrides.clear()


def _make_token(user_id: int = 1) -> str:
    from src.services.auth import create_access_token
    return create_access_token(
        subject=str(user_id), role="user",
        secret_key=get_base_settings().APP_AUTH_SECRET_KEY,
    )


def test_ws_rejects_missing_token(client):
    """无 token 连接 → 服务端 close(4401), 客户端 receive 触发 WebSocketDisconnect."""
    from starlette.websockets import WebSocketDisconnect
    with client.websocket_connect("/ws") as ws:
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_text()
        assert exc.value.code == 4401


def test_ws_rejects_invalid_token(client):
    """非法 token → close(4401)."""
    from starlette.websockets import WebSocketDisconnect
    with client.websocket_connect("/ws?token=garbage") as ws:
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_text()
        assert exc.value.code == 4401


def test_ws_accepts_valid_token(client):
    """合法 token → 成功握手 (服务端接受连接)."""
    token = _make_token()
    with client.websocket_connect(f"/ws?token={token}") as ws:
        # 握手成功本身就是验证 (没有 catchup, 直接进入接收循环)
        # 服务端不主动发欢迎消息, 这里立即关闭即可
        pass


def test_ws_replays_outbox_when_since_provided(client, engine):
    """握手时带 ?since= → 回放 event_outbox > since 的行."""
    from src.events.ids import new_event_id

    # 种子 3 条 published 事件, 第 2 条作为 since 边界
    with Session(engine) as s:
        eids = []
        for i in range(3):
            eid = new_event_id()
            eids.append(eid)
            s.add(EventOutbox(
                aggregate_type="x", aggregate_id=i,
                event_type="position.opened",
                event_id=eid,
                payload_json={"event_id": eid, "i": i},
                published_at=datetime.now(tz=timezone.utc),
            ))
        s.commit()

    token = _make_token()
    since = eids[0]  # 跳过第 0 条, 应该收到第 1 条 + 第 2 条
    received: list[str] = []
    with client.websocket_connect(f"/ws?token={token}&since={since}") as ws:
        # 接 2 条 replay; 第 3 个 receive 会阻塞实时通道, 这里只取已 enqueue 的
        for _ in range(2):
            msg = ws.receive_text()
            received.append(msg)

    assert len(received) == 2
    import json as _json
    parsed = [_json.loads(m) for m in received]
    received_ids = {p["event_id"] for p in parsed}
    assert eids[1] in received_ids
    assert eids[2] in received_ids
    assert eids[0] not in received_ids  # since 边界排除
