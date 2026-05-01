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
async def test_runtime_config_update_requires_admin(monkeypatch):
    from src.controllers import router as router_module

    monkeypatch.setattr(
        router_module,
        "get_current_user",
        lambda: SimpleNamespace(id=1, username="u1", role="user", status="active"),
    )

    def override_db():
        yield DummyDB()

    app.dependency_overrides[get_db] = override_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/config/runtime",
                json={"trading_mode": "testnet"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401 or response.status_code == 403


@pytest.mark.asyncio
async def test_runtime_config_update_allows_admin(monkeypatch):
    from src.controllers import router as router_module
    from src.controllers.api.v1.system import runtime_config as runtime_module

    db = DummyDB()
    updates = []
    refresh_calls = []

    monkeypatch.setattr(
        runtime_module,
        "get_base_settings",
        lambda: SimpleNamespace(LLM_API_KEY="env-llm", APP_CONFIG_MASTER_KEY="test-key", TRADING_MODE=TradingMode.TESTNET),
    )
    monkeypatch.setattr(
        runtime_module,
        "get_settings",
        lambda: SimpleNamespace(
            TRADING_MODE=TradingMode.TESTNET,
            LLM_BASE_URL="https://api.deepseek.com/v1",
            LLM_MODEL="deepseek-chat",
            MAX_POSITION_SIZE_PCT=0.3,
            MAX_DAILY_LOSS_PCT=0.05,
            MAX_CONSECUTIVE_LOSSES=6,
            MAX_SINGLE_RISK_PCT=0.03,
            LLM_API_KEY="db-llm",
        ),
    )
    monkeypatch.setattr(runtime_module, "build_fernet", lambda key: object())
    monkeypatch.setattr(
        runtime_module,
        "upsert_system_setting",
        lambda db, *, key, value, fernet, description=None: updates.append((key, value, description)),
    )
    monkeypatch.setattr(
        runtime_module,
        "apply_runtime_settings_refresh",
        lambda db, *, master_key, default_trading_mode: refresh_calls.append((master_key, default_trading_mode.value)),
    )
    monkeypatch.setattr(
        runtime_module,
        "get_runtime_config_manager",
        lambda: SimpleNamespace(
            get_raw=lambda: {
                "binance.testnet.api_key": "tk",
                "binance.testnet.api_secret": "ts",
            }
        ),
    )

    async def override_admin():
        return SimpleNamespace(id=99, username="admin", role="admin", status="active")

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[router_module.require_admin] = override_admin
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/config/runtime",
                json={"trading_mode": "testnet", "max_consecutive_losses": 4},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert db.committed is True
    assert ("runtime.trading_mode", "testnet", "当前运行模式") in updates
    assert ("risk.max_consecutive_losses", 4, "连续亏损熔断笔数") in updates
    assert refresh_calls == [("test-key", "testnet")]
