"""dependencies.get_current_user 鉴权异常 → 401 单测.

Code review (post Plan5 minor) 发现: decode_access_token 抛 ValueError /
sub 不可转 int 时, FastAPI 默认会返 500 而不是 401, 导致前端 401 自动登出
逻辑不触发. 这里保护这条不变量.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.app.dependencies import get_current_user
from src.shared.db import get_db
from src.shared.models import Base


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    app = FastAPI()

    @app.get("/api/protected")
    def _protected(user=pytest.importorskip("fastapi").Depends(get_current_user)):
        return {"id": user.id}

    def _override():
        s = Session(engine)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_no_authorization_header_returns_401(client):
    r = client.get("/api/protected")
    assert r.status_code == 401


def test_non_bearer_authorization_returns_401(client):
    r = client.get("/api/protected", headers={"Authorization": "Basic xyz"})
    assert r.status_code == 401


def test_garbage_jwt_returns_401_not_500(client):
    """关键回归: decode_access_token 抛 ValueError 必须翻成 401."""
    r = client.get("/api/protected", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401, f"got {r.status_code}: {r.text}"


def test_jwt_with_wrong_signature_returns_401(client):
    """另一种 ValueError 触发路径: 用错误的 secret 签的 token."""
    from src.services.auth import create_access_token
    bad_token = create_access_token(
        subject="1", role="user", secret_key="wrong-secret-key",
    )
    r = client.get("/api/protected", headers={"Authorization": f"Bearer {bad_token}"})
    assert r.status_code == 401


def test_jwt_with_non_int_sub_returns_401(client):
    """sub 不是数字串时 int(user_id) 会抛 ValueError, 必须 401 不能 500."""
    from src.services.auth import create_access_token
    from src.shared.config import get_base_settings
    bad_sub_token = create_access_token(
        subject="not-a-number", role="user",
        secret_key=get_base_settings().APP_AUTH_SECRET_KEY,
    )
    r = client.get(
        "/api/protected",
        headers={"Authorization": f"Bearer {bad_sub_token}"},
    )
    assert r.status_code == 401
