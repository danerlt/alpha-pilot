"""2FA (TOTP) 全流程测试 (handoff 3.7)。"""
from __future__ import annotations

import os

import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app import app
from src.db.session import get_db
from src.models import Base
from src.models.user import User
from src.services.auth import hash_password

_EMAIL = "twofa@example.com"
_PASSWORD = "pass-2fa-123456"


@pytest.fixture
def client():
    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        s.add(User(
            username="twofa", email=_EMAIL,
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
    yield TestClient(app), eng
    app.dependency_overrides.clear()


def _login(cli, password=_PASSWORD):
    return cli.post("/api/auth/login", json={"email": _EMAIL, "password": password})


def test_full_2fa_flow(client):
    cli, eng = client
    # 1. 登录 (未启用 2FA → 直接拿 token)
    r = _login(cli)
    assert r.json()["data"]["requires_2fa"] is False

    # 2. setup → secret + uri
    r = cli.post("/api/auth/2fa/setup")
    data = r.json()["data"]
    secret = data["secret"]
    assert "otpauth://" in data["otpauth_uri"]
    # secret 加密入库, 不是明文
    with Session(eng) as s:
        u = s.query(User).filter(User.email == _EMAIL).one()
        assert u.totp_secret and secret not in u.totp_secret
        assert u.two_fa_enabled is False

    # 3. verify 错误 code → 拒
    assert cli.post("/api/auth/2fa/verify", json={"code": "000000"}).json()["success"] is False
    # 正确 code → 启用
    code = pyotp.TOTP(secret).now()
    r = cli.post("/api/auth/2fa/verify", json={"code": code})
    assert r.json()["data"]["two_fa_enabled"] is True

    # 4. 重新登录 → 二段式: 无 token 无 cookie, 有票据
    fresh = TestClient(app)
    r = fresh.post("/api/auth/login", json={"email": _EMAIL, "password": _PASSWORD})
    body = r.json()["data"]
    assert body["requires_2fa"] is True
    assert body["access_token"] is None
    assert "ap_token" not in r.headers.get("set-cookie", "")
    ticket = body["two_fa_token"]

    # 5. 二段: 错 code 拒
    r = fresh.post("/api/auth/2fa/login", json={"two_fa_token": ticket, "code": "000000"})
    assert r.json()["success"] is False
    # 正确 code → 正式 token + cookie
    code = pyotp.TOTP(secret).now()
    r = fresh.post("/api/auth/2fa/login", json={"two_fa_token": ticket, "code": code})
    body = r.json()["data"]
    assert body["access_token"]
    assert body["user"]["two_fa_enabled"] is True
    assert "ap_token=" in r.headers.get("set-cookie", "")
    # cookie 直接可用
    assert fresh.get("/api/auth/me").json()["data"]["email"] == _EMAIL

    # 6. disable (需有效 code)
    code = pyotp.TOTP(secret).now()
    r = fresh.post("/api/auth/2fa/disable", json={"code": code})
    assert r.json()["data"]["two_fa_enabled"] is False


def test_2fa_login_rejects_normal_token_as_ticket(client):
    """守卫: 正式 access_token 不能当 2fa 票据用 (scope 校验)。"""
    cli, _ = client
    token = _login(cli).json()["data"]["access_token"]
    r = cli.post("/api/auth/2fa/login", json={"two_fa_token": token, "code": "000000"})
    assert r.json()["success"] is False
    assert r.json()["code"] == "400003"
