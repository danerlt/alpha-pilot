from __future__ import annotations

import json
import logging
import threading
from functools import lru_cache
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

from src.common.enums import TradingMode
from src.models.system_setting import SystemSetting

logger = logging.getLogger(__name__)

RUNTIME_MODE_KEY = "runtime.trading_mode"
BINANCE_TESTNET_API_KEY = "binance.testnet.api_key"
BINANCE_TESTNET_API_SECRET = "binance.testnet.api_secret"
BINANCE_MAINNET_API_KEY = "binance.mainnet.api_key"
BINANCE_MAINNET_API_SECRET = "binance.mainnet.api_secret"
LLM_API_KEY = "llm.api_key"
LLM_BASE_URL = "llm.base_url"
LLM_MODEL = "llm.model"
MAX_POSITION_SIZE_PCT = "risk.max_position_size_pct"
MAX_DAILY_LOSS_PCT = "risk.max_daily_loss_pct"
MAX_CONSECUTIVE_LOSSES = "risk.max_consecutive_losses"
MAX_SINGLE_RISK_PCT = "risk.max_single_risk_pct"

SECRET_KEYS = {
    BINANCE_TESTNET_API_KEY,
    BINANCE_TESTNET_API_SECRET,
    BINANCE_MAINNET_API_KEY,
    BINANCE_MAINNET_API_SECRET,
    LLM_API_KEY,
}


class RuntimeConfigManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._raw: dict[str, Any] = {}
        self._overrides: dict[str, Any] = {}

    def get_overrides(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._overrides)

    def get_raw(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._raw)

    def refresh_from_db(self, db: Session, fernet: Fernet, default_trading_mode: TradingMode) -> dict[str, Any]:
        rows = db.query(SystemSetting).order_by(SystemSetting.key.asc()).all()
        raw: dict[str, Any] = {}

        for row in rows:
            if row.is_secret:
                if not row.encrypted_value:
                    continue
                try:
                    raw[row.key] = fernet.decrypt(row.encrypted_value.encode()).decode()
                except InvalidToken:
                    logger.error("Failed to decrypt system setting: %s", row.key)
            else:
                raw[row.key] = row.value_json

        active_mode = raw.get(RUNTIME_MODE_KEY, default_trading_mode.value)
        if active_mode not in {TradingMode.TESTNET.value, TradingMode.MAINNET.value}:
            active_mode = default_trading_mode.value

        mode_prefix = f"binance.{active_mode}"
        overrides: dict[str, Any] = {
            "TRADING_MODE": active_mode,
        }

        direct_map = {
            LLM_BASE_URL: "LLM_BASE_URL",
            LLM_MODEL: "LLM_MODEL",
            MAX_POSITION_SIZE_PCT: "MAX_POSITION_SIZE_PCT",
            MAX_DAILY_LOSS_PCT: "MAX_DAILY_LOSS_PCT",
            MAX_CONSECUTIVE_LOSSES: "MAX_CONSECUTIVE_LOSSES",
            MAX_SINGLE_RISK_PCT: "MAX_SINGLE_RISK_PCT",
        }
        for key, field in direct_map.items():
            if key in raw and raw[key] is not None:
                overrides[field] = raw[key]

        api_key = raw.get(f"{mode_prefix}.api_key")
        api_secret = raw.get(f"{mode_prefix}.api_secret")
        if api_key:
            overrides["BINANCE_API_KEY"] = api_key
        if api_secret:
            overrides["BINANCE_API_SECRET"] = api_secret
        if raw.get(LLM_API_KEY):
            overrides["LLM_API_KEY"] = raw[LLM_API_KEY]

        with self._lock:
            self._raw = raw
            self._overrides = overrides
        return dict(overrides)


@lru_cache(maxsize=1)
def get_runtime_config_manager() -> RuntimeConfigManager:
    return RuntimeConfigManager()


def build_fernet(master_key: str) -> Fernet:
    return Fernet(master_key.encode())


def serialize_secret(value: str, fernet: Fernet) -> str:
    return fernet.encrypt(value.encode()).decode()


def coerce_setting_value(key: str, value: Any) -> Any:
    if key in {MAX_POSITION_SIZE_PCT, MAX_DAILY_LOSS_PCT, MAX_SINGLE_RISK_PCT}:
        return float(value)
    if key == MAX_CONSECUTIVE_LOSSES:
        return int(value)
    if key == RUNTIME_MODE_KEY:
        return TradingMode(value).value
    return value


def upsert_system_setting(
    db: Session,
    *,
    key: str,
    value: Any,
    fernet: Fernet,
    description: str | None = None,
) -> SystemSetting:
    row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if row is None:
        row = SystemSetting(key=key)
        db.add(row)

    row.description = description
    row.is_secret = key in SECRET_KEYS
    normalized = coerce_setting_value(key, value)

    if row.is_secret:
        row.value_json = None
        row.encrypted_value = serialize_secret(str(normalized), fernet)
    else:
        row.value_json = json.loads(json.dumps(normalized))
        row.encrypted_value = None

    db.flush()
    return row


def apply_runtime_settings_refresh(db: Session, *, master_key: str, default_trading_mode: TradingMode) -> dict[str, Any]:
    from src.core.exchange.binance_client import get_binance_client

    manager = get_runtime_config_manager()
    overrides = manager.refresh_from_db(db, build_fernet(master_key), default_trading_mode)
    get_binance_client.cache_clear()
    return overrides
