from src.configs.app_configs import AppConfig as Settings
from src.configs.app_configs import can_call_binance, can_call_llm, get_runtime_credential_status


def test_runtime_credential_status_detects_placeholders():
    settings = Settings(_env_file=None)
    diag = get_runtime_credential_status(settings)

    assert diag["binance"]["configured"] is False
    assert diag["binance"]["reason"] == "placeholder_or_missing"
    assert diag["llm"]["configured"] is False
    assert diag["llm"]["reason"] == "placeholder_or_missing"
    assert can_call_binance(settings) is False
    assert can_call_llm(settings) is False


def test_runtime_credential_status_accepts_non_placeholder_values():
    settings = Settings(
        _env_file=None,
        BINANCE_API_KEY="real-binance-key",
        BINANCE_API_SECRET="real-binance-secret",
        LLM_API_KEY="real-llm-key",
    )
    diag = get_runtime_credential_status(settings)

    assert diag["binance"]["configured"] is True
    assert diag["llm"]["configured"] is True
    assert can_call_binance(settings) is True
    assert can_call_llm(settings) is True
