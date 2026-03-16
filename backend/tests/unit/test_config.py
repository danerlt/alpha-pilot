import pytest
from src.shared.config import Settings
from src.shared.enums import TradingMode, Action, EntryType, StrategyMode, RegimeType, GuardResult


def test_settings_defaults():
    s = Settings(
        BINANCE_API_KEY="key",
        BINANCE_API_SECRET="secret",
        LLM_API_KEY="llmkey",
        DATABASE_URL="postgresql://user:pass@localhost/db",
        REDIS_URL="redis://localhost:6379/0",
    )
    assert s.TRADING_MODE == TradingMode.TESTNET
    assert s.LLM_TIMEOUT_SECONDS == 30
    assert s.MAX_POSITION_SIZE_PCT == 0.20
    assert s.MAX_DAILY_LOSS_PCT == 0.03
    assert s.MAX_CONSECUTIVE_LOSSES == 3
    assert s.MAX_SINGLE_RISK_PCT == 0.01


def test_settings_safe_placeholders_for_tests(monkeypatch):
    for key in [
        "BINANCE_API_KEY",
        "BINANCE_API_SECRET",
        "LLM_API_KEY",
        "DATABASE_URL",
        "REDIS_URL",
    ]:
        monkeypatch.delenv(key, raising=False)

    s = Settings(_env_file=None)
    assert s.BINANCE_API_KEY == "test-binance-api-key"
    assert s.BINANCE_API_SECRET == "test-binance-api-secret"
    assert s.LLM_API_KEY == "test-llm-api-key"
    assert s.DATABASE_URL == "sqlite:///./alphapilot.db"
    assert s.REDIS_URL == "redis://localhost:6379/0"


def test_trading_mode_enum():
    assert TradingMode.TESTNET.value == "testnet"
    assert TradingMode.MAINNET.value == "mainnet"


def test_action_enum():
    assert Action.OPEN_LONG.value == "OPEN_LONG"
    assert Action.CLOSE_LONG.value == "CLOSE_LONG"
    assert Action.HOLD.value == "HOLD"
    # V0.1 仅做多，不应有 OPEN_SHORT
    assert not hasattr(Action, "OPEN_SHORT")


def test_guard_result_enum():
    assert GuardResult.PASS.value == "PASS"
    assert GuardResult.REJECT.value == "REJECT"
    assert GuardResult.DEGRADE.value == "DEGRADE"


def test_regime_type_enum():
    assert RegimeType.TRENDING_UP.value == "trending_up"
    assert RegimeType.TRENDING_DOWN.value == "trending_down"
    assert RegimeType.RANGING.value == "ranging"
    assert RegimeType.CHAOTIC.value == "chaotic"
