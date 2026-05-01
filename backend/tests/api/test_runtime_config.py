from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from src.app import app
from src.shared.db import get_db
from src.shared.enums import TradingMode


class DummyDB:
    def __init__(self):
        self.committed = False

    def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_get_runtime_config_masks_secrets_and_reports_config_state(monkeypatch):
    from src.controllers.api.v1.system import runtime_config as router_module

    monkeypatch.setattr(
        router_module,
        "get_base_settings",
        lambda: SimpleNamespace(LLM_API_KEY="env-llm", APP_CONFIG_MASTER_KEY="test-key", TRADING_MODE=TradingMode.TESTNET),
    )
    monkeypatch.setattr(
        router_module,
        "get_settings",
        lambda: SimpleNamespace(
            TRADING_MODE=TradingMode.MAINNET,
            LLM_BASE_URL="https://api.deepseek.com/v1",
            LLM_MODEL="deepseek-chat",
            MAX_POSITION_SIZE_PCT=0.25,
            MAX_DAILY_LOSS_PCT=0.04,
            MAX_CONSECUTIVE_LOSSES=5,
            MAX_SINGLE_RISK_PCT=0.02,
            LLM_API_KEY="db-llm",
        ),
    )
    monkeypatch.setattr(
        router_module,
        "get_runtime_config_manager",
        lambda: SimpleNamespace(
            get_raw=lambda: {
                "binance.testnet.api_key": "tk",
                "binance.testnet.api_secret": "ts",
                "binance.mainnet.api_key": "mk",
                "binance.mainnet.api_secret": "ms",
            }
        ),
    )

    def override_db():
        yield DummyDB()

    app.dependency_overrides[get_db] = override_db
    # post-Plan5 安全审计 C4: GET /api/config/runtime 现在 require_admin
    app.dependency_overrides[router_module.require_admin] = lambda: SimpleNamespace(
        id=1, username="admin", role="admin", status="active",
    )
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/config/runtime")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["trading_mode"] == "mainnet"
    assert data["binance_testnet_configured"] is True
    assert data["binance_mainnet_configured"] is True
    assert data["llm_api_key_configured"] is True
    assert data["config_source"] == "database_overrides"
    assert "api_secret" not in str(data).lower()


@pytest.mark.asyncio
async def test_get_runtime_config_requires_admin():
    """post-Plan5 安全审计 C4: 没鉴权时直接 401 (FastAPI 默认行为是无 dep override)."""
    def override_db():
        yield DummyDB()

    app.dependency_overrides[get_db] = override_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/config/runtime")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_runtime_config_persists_and_refreshes(monkeypatch):
    from src.controllers.api.v1.system import runtime_config as router_module

    db = DummyDB()
    updates = []
    refresh_calls = []

    monkeypatch.setattr(
        router_module,
        "get_base_settings",
        lambda: SimpleNamespace(LLM_API_KEY="env-llm", APP_CONFIG_MASTER_KEY="test-key", TRADING_MODE=TradingMode.TESTNET),
    )
    monkeypatch.setattr(
        router_module,
        "get_settings",
        lambda: SimpleNamespace(
            TRADING_MODE=TradingMode.MAINNET,
            LLM_BASE_URL="https://api.deepseek.com/v1",
            LLM_MODEL="deepseek-chat",
            MAX_POSITION_SIZE_PCT=0.3,
            MAX_DAILY_LOSS_PCT=0.05,
            MAX_CONSECUTIVE_LOSSES=6,
            MAX_SINGLE_RISK_PCT=0.03,
            LLM_API_KEY="db-llm",
        ),
    )
    monkeypatch.setattr(router_module, "build_fernet", lambda key: object())
    monkeypatch.setattr(
        router_module,
        "upsert_system_setting",
        lambda db, *, key, value, fernet, description=None: updates.append((key, value, description)),
    )
    monkeypatch.setattr(
        router_module,
        "apply_runtime_settings_refresh",
        lambda db, *, master_key, default_trading_mode: refresh_calls.append((master_key, default_trading_mode.value)),
    )
    monkeypatch.setattr(
        router_module,
        "get_runtime_config_manager",
        lambda: SimpleNamespace(
            get_raw=lambda: {
                "binance.testnet.api_key": "tk",
                "binance.testnet.api_secret": "ts",
                "binance.mainnet.api_key": "mk",
                "binance.mainnet.api_secret": "ms",
                "llm.api_key": "db-llm",
            }
        ),
    )

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[router_module.require_admin] = lambda: SimpleNamespace(id=1, username="admin", role="admin", status="active")
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/config/runtime",
                json={
                    "trading_mode": "mainnet",
                    "binance_mainnet_api_key": "new-main-key",
                    "binance_mainnet_api_secret": "new-main-secret",
                    "max_daily_loss_pct": 0.05,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert db.committed is True
    assert ("runtime.trading_mode", "mainnet", "当前运行模式") in updates
    assert ("binance.mainnet.api_key", "new-main-key", "Binance Mainnet API Key") in updates
    assert ("binance.mainnet.api_secret", "new-main-secret", "Binance Mainnet API Secret") in updates
    assert ("risk.max_daily_loss_pct", 0.05, "最大日亏损比例") in updates
    assert refresh_calls == [("test-key", "testnet")]
    data = response.json()
    assert data["trading_mode"] == "mainnet"
    assert data["binance_mainnet_configured"] is True
    assert "new-main-secret" not in str(data)


@pytest.mark.asyncio
async def test_update_runtime_config_rejects_empty_payload_for_admin():
    from src.controllers.api.v1.system import runtime_config as router_module

    def override_db():
        yield DummyDB()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[router_module.require_admin] = lambda: SimpleNamespace(id=1, username="admin", role="admin", status="active")
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/config/runtime", json={})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "No config fields provided"
