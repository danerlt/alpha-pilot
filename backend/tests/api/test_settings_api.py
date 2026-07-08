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
    # settings PUT 会触发 runtime refresh 写回全局 settings 单例 —— 快照恢复防污染
    from src.configs.app_configs import get_settings

    settings = get_settings()
    _keep_fields = (
        "TRADING_MODE", "BINANCE_API_KEY", "BINANCE_API_SECRET",
        "LLM_API_KEY", "LLM_MODEL", "LLM_BASE_URL",
        "NOTIFY_ENABLED", "NOTIFY_MIN_SEVERITY",
        "NOTIFY_TELEGRAM_BOT_TOKEN", "NOTIFY_TELEGRAM_CHAT_ID",
        "MAX_POSITION_SIZE_PCT", "MAX_DAILY_LOSS_PCT",
        "MAX_CONSECUTIVE_LOSSES", "MAX_SINGLE_RISK_PCT",
    )
    _snapshot = {f: getattr(settings, f) for f in _keep_fields}

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
    for f, v in _snapshot.items():
        setattr(settings, f, v)


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


def test_put_exchange_does_not_switch_running_network(admin_client):
    """配 key 不切系统运行网络 —— 只存对应网络槽位。"""
    cli, _ = admin_client
    before = cli.get("/api/settings/exchange").json()["data"]["network"]
    other = "mainnet" if before == "testnet" else "testnet"
    # 给"另一个"网络配 key，不应把系统运行网络切过去
    cli.put("/api/settings/exchange", json={
        "network": other, "api_key": "OTHERNETKEY9999XX", "api_secret": "OSEC12345678",
    })
    after = cli.get("/api/settings/exchange").json()["data"]["network"]
    assert after == before  # 运行网络不变
    # 但 key 确实存进了 other 槽位
    data = cli.get("/api/settings/exchange").json()["data"]
    assert data[other]["api_key_masked"] == "****99XX"


def test_set_active_network_switches_running_network(admin_client):
    """切换运行网络是独立端点。"""
    cli, _ = admin_client
    cur = cli.get("/api/settings/exchange").json()["data"]["network"]
    target = "mainnet" if cur == "testnet" else "testnet"
    r = cli.post("/api/settings/exchange/active-network", json={"network": target})
    assert r.status_code == 200
    assert r.json()["data"]["network"] == target


def test_exchange_two_networks_stored_and_read_separately(admin_client):
    """主网/测试网 key 分开存、分开读 — GET 一次返回两网络各自脱敏, 不串。"""
    cli, _ = admin_client
    cli.put("/api/settings/exchange", json={
        "network": "testnet", "api_key": "TESTNETKEY0000AAAA", "api_secret": "TSEC12345678",
    })
    cli.put("/api/settings/exchange", json={
        "network": "mainnet", "api_key": "MAINNETKEY1111BBBB", "api_secret": "MSEC12345678",
    })
    data = cli.get("/api/settings/exchange").json()["data"]
    assert data["testnet"]["api_key_masked"] == "****AAAA"
    assert data["mainnet"]["api_key_masked"] == "****BBBB"
    assert data["testnet"]["has_secret"] is True
    assert data["mainnet"]["has_secret"] is True
    # 两网络脱敏互不相同 (老板反馈的"主网测试网显示同一个"回归防护)
    assert data["testnet"]["api_key_masked"] != data["mainnet"]["api_key_masked"]


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


def test_notifications_telegram_token_masked(admin_client):
    cli, eng = admin_client
    r = cli.put("/api/settings/notifications", json={
        "telegram_bot_token": "123456:AAHsecretXYZ9999",
        "telegram_chat_id": "-1001234",
        "min_severity": "critical",
    })
    data = r.json()["data"]
    assert data["telegram_bot_token_masked"] == "****9999"
    assert data["telegram_chat_id"] == "-1001234"
    assert data["min_severity"] == "critical"
    assert "AAHsecret" not in r.text  # 无明文回显
    # DB 加密存储
    from src.models.system_setting import SystemSetting

    with Session(eng) as s:
        row = s.query(SystemSetting).filter(
            SystemSetting.key == "notify.telegram.bot_token"
        ).one()
        assert row.is_secret is True
        assert "AAHsecret" not in (row.encrypted_value or "")
