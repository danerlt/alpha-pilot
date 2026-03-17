from __future__ import annotations

from src.shared.config import Settings
from src.shared.enums import TradingMode

PLACEHOLDER_BINANCE_KEYS = {
    "test-binance-api-key",
    "test-binance-api-secret",
    "",
}
PLACEHOLDER_LLM_KEYS = {
    "test-llm-api-key",
    "",
}


def _status(configured: bool, reason: str | None = None) -> dict[str, object]:
    return {
        "configured": configured,
        "reason": reason,
    }


def get_runtime_credential_status(settings: Settings) -> dict[str, dict[str, object]]:
    binance_key = getattr(settings, "BINANCE_API_KEY", "") or ""
    binance_secret = getattr(settings, "BINANCE_API_SECRET", "") or ""
    llm_key = getattr(settings, "LLM_API_KEY", "") or ""

    if binance_key in PLACEHOLDER_BINANCE_KEYS or binance_secret in PLACEHOLDER_BINANCE_KEYS:
        binance = _status(False, "placeholder_or_missing")
    else:
        binance = _status(True, None)

    if llm_key in PLACEHOLDER_LLM_KEYS:
        llm = _status(False, "placeholder_or_missing")
    else:
        llm = _status(True, None)

    return {
        "binance": {
            **binance,
            "mode": getattr(settings, "TRADING_MODE", TradingMode.TESTNET).value if isinstance(getattr(settings, "TRADING_MODE", TradingMode.TESTNET), TradingMode) else str(getattr(settings, "TRADING_MODE", TradingMode.TESTNET)),
        },
        "llm": {
            **llm,
            "provider": getattr(settings, "LLM_PROVIDER", "unknown"),
            "model": getattr(settings, "LLM_MODEL", "unknown"),
        },
    }


def can_call_binance(settings: Settings) -> bool:
    status = get_runtime_credential_status(settings)["binance"]
    return bool(status["configured"])


def can_call_llm(settings: Settings) -> bool:
    status = get_runtime_credential_status(settings)["llm"]
    return bool(status["configured"])
