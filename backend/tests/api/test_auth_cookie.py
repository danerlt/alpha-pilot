"""B3 认证升级测试: httpOnly cookie 下发/回退/登出 + 权限矩阵端点。"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app import app
from src.db.session import get_db
from src.models import Base
from src.models.user import User
from src.services.auth import hash_password

_EMAIL = "cookie-test@example.com"
_PASSWORD = "s3cret-pass-123"


@pytest.fixture
def client():
    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        s.add(User(
            username="cookieuser", email=_EMAIL,
            password_hash=hash_password(_PASSWORD),
            role="admin", status="active",
        ))
        s.commit()

    def _override():
        s = Session(eng)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    yield TestClient(app)
    app.dependency_overrides.clear()


def _login(cli: TestClient):
    return cli.post("/api/auth/login", json={"email": _EMAIL, "password": _PASSWORD})


def test_login_sets_httponly_cookie(client):
    r = _login(client)
    assert r.status_code == 200
    assert r.json()["success"] is True
    set_cookie = r.headers.get("set-cookie", "")
    assert "ap_token=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie or "samesite=lax" in set_cookie.lower()
    # Bearer 并存: body 里仍有 access_token
    assert r.json()["data"]["access_token"]


def test_cookie_authenticates_without_bearer_header(client):
    _login(client)  # TestClient 自动保存 cookie
    r = client.get("/api/auth/me")  # 不带 Authorization 头
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["email"] == _EMAIL


def test_bearer_header_still_works(client):
    token = _login(client).json()["data"]["access_token"]
    fresh = TestClient(app)  # 无 cookie
    r = fresh.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.json()["success"] is True


def test_logout_clears_cookie(client):
    _login(client)
    r = client.post("/api/auth/logout")
    assert r.json()["success"] is True
    r2 = client.get("/api/auth/me")
    assert r2.json()["code"] == "400003"


def test_roles_matrix_endpoint(client):
    _login(client)
    r = client.get("/api/admin/roles")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["roles"] == ["owner", "admin", "trader", "viewer"]
    assert data["role_aliases"] == {"user": "trader"}
    assert data["current_role"] == "admin"
    groups = {g["group"] for g in data["matrix"]}
    assert groups == {"交易", "策略", "系统"}
    # 抽查关键权限: 修改硬风控 trader 无权
    risk_item = next(
        i for g in data["matrix"] for i in g["items"]
        if i["key"] == "risk.edit_hard_limits"
    )
    assert risk_item["admin"] is True and risk_item["trader"] is False


def test_roles_rejects_anonymous():
    r = TestClient(app).get("/api/admin/roles")
    assert r.json()["code"] == "400003"
