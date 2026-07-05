"""/api/settings 三分区测试 (handoff 3.6): 脱敏/权限/测试连接。"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app import app
from src.controllers.dependencies import get_current_user
from src.db.session import get_db
from src.models import Base


@pytest.fixture
def admin_client():
    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)

    def _override():
        s = Session(eng)
        try:
            yield s
        finally:
            s.close()

    from types import SimpleNamespace

    app.dependency_overrides[get_db] = _override
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="admin", role="admin", status="active",
    )
    yield TestClient(app), eng
    app.dependency_overrides.clear()


def test_exchange_put_returns_masked_never_plaintext(admin_client):
    cli, _ = admin_client
    secret_key = "AKIAEXAMPLEKEY123456"
    r = cli.put("/api/settings/exchange", json={
        "network": "testnet", "api_key": secret_key, "api_secret": "SECRETXYZ7890",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["network"] == "testnet"
    assert data["api_key_masked"] == "****3456"
    assert data["has_secret"] is True
    assert secret_key not in r.text  # 全链路无明文回显
    # GET 同样脱敏
    r2 = cli.get("/api/settings/exchange")
    assert secret_key not in r2.text
    assert r2.json()["data"]["api_key_masked"] == "****3456"


def test_exchange_secret_encrypted_in_db(admin_client):
    cli, eng = admin_client
    cli.put("/api/settings/exchange", json={
        "network": "testnet", "api_key": "PLAINKEY12345678",
    })
    from src.models.system_setting import SystemSetting

    with Session(eng) as s:
        row = s.query(SystemSetting).filter(
            SystemSetting.key == "binance.testnet.api_key"
        ).one()
        assert row.is_secret is True
        assert row.value_json is None
        assert "PLAINKEY" not in (row.encrypted_value or "")


def test_llm_roundtrip_and_masking(admin_client):
    cli, _ = admin_client
    r = cli.put("/api/settings/llm", json={
        "model": "deepseek-v4-pro", "api_key": "sk-secret-abcd9999",
        "temperature": 0.25, "agent_models": {"decision": "deepseek-v4-pro"},
    })
    data = r.json()["data"]
    assert data["model"] == "deepseek-v4-pro"
    assert data["api_key_masked"] == "****9999"
    assert data["temperature"] == 0.25
    assert data["agent_models"] == {"decision": "deepseek-v4-pro"}
    assert "sk-secret" not in r.text


def test_notifications_roundtrip(admin_client):
    cli, _ = admin_client
    r = cli.put("/api/settings/notifications", json={
        "channels": {"telegram": True},
        "subscriptions": {"daily_report": True},
    })
    data = r.json()["data"]
    assert data["channels"]["telegram"] is True
    assert data["channels"]["discord"] is False  # 默认保留
    assert data["subscriptions"]["daily_report"] is True
    assert data["subscriptions"]["circuit_breaker"] is True


def test_settings_require_admin():
    def _user():
        from types import SimpleNamespace

        return SimpleNamespace(id=2, username="u", role="user", status="active")

    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)

    def _override():
        s = Session(eng)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    app.dependency_overrides[get_current_user] = _user
    try:
        cli = TestClient(app)
        assert cli.get("/api/settings/exchange").json()["code"] == "400004"
    finally:
        app.dependency_overrides.clear()
