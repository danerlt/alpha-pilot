"""Runtime config — /api/config/runtime (GET / POST)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from src.common.api_response import api_response
from src.common.exception.errors import ParamsException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.controllers.dependencies import require_admin
from src.shared.config import get_base_settings, get_settings
from src.shared.config_diagnostics import get_runtime_credential_status
from src.shared.db import get_db
from src.shared.enums import TradingMode
from src.shared.runtime_config import (
    BINANCE_MAINNET_API_KEY,
    BINANCE_MAINNET_API_SECRET,
    BINANCE_TESTNET_API_KEY,
    BINANCE_TESTNET_API_SECRET,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    MAX_CONSECUTIVE_LOSSES,
    MAX_DAILY_LOSS_PCT,
    MAX_POSITION_SIZE_PCT,
    MAX_SINGLE_RISK_PCT,
    RUNTIME_MODE_KEY,
    apply_runtime_settings_refresh,
    build_fernet,
    get_runtime_config_manager,
    upsert_system_setting,
)

router = APIRouter(prefix="/api/config", tags=["config"])


class RuntimeConfigUpdate(BaseModel):
    trading_mode: TradingMode | None = None
    binance_testnet_api_key: str | None = None
    binance_testnet_api_secret: str | None = None
    binance_mainnet_api_key: str | None = None
    binance_mainnet_api_secret: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    max_position_size_pct: float | None = None
    max_daily_loss_pct: float | None = None
    max_consecutive_losses: int | None = None
    max_single_risk_pct: float | None = None


@router.get("/runtime")
@api_response()
def get_runtime_config(
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    return _build_runtime_config_payload(db)


def _build_runtime_config_payload(db: Session) -> dict:
    """构造 runtime config 数据 payload（被 GET 和 POST 共享，避免相互调用导致双层包装）。"""
    base_settings = get_base_settings()
    settings = get_settings()
    raw = get_runtime_config_manager().get_raw()

    runtime_credentials = get_runtime_credential_status(settings)
    return {
        "trading_mode": settings.TRADING_MODE.value,
        "llm_base_url": settings.LLM_BASE_URL,
        "llm_model": settings.LLM_MODEL,
        "max_position_size_pct": settings.MAX_POSITION_SIZE_PCT,
        "max_daily_loss_pct": settings.MAX_DAILY_LOSS_PCT,
        "max_consecutive_losses": settings.MAX_CONSECUTIVE_LOSSES,
        "max_single_risk_pct": settings.MAX_SINGLE_RISK_PCT,
        "binance_testnet_configured": bool(raw.get(BINANCE_TESTNET_API_KEY) and raw.get(BINANCE_TESTNET_API_SECRET)),
        "binance_mainnet_configured": bool(raw.get(BINANCE_MAINNET_API_KEY) and raw.get(BINANCE_MAINNET_API_SECRET)),
        "llm_api_key_configured": bool(raw.get(LLM_API_KEY)) or settings.LLM_API_KEY != base_settings.LLM_API_KEY,
        "config_source": "database_overrides" if raw else "env_defaults",
        "runtime_credentials": runtime_credentials,
    }


@router.post("/runtime")
@api_response()
def update_runtime_config(
    payload: RuntimeConfigUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    base_settings = get_base_settings()
    fernet_key = base_settings.APP_CONFIG_MASTER_KEY
    fernet = build_fernet(fernet_key)

    update_map: list[tuple[str, Any, str]] = []
    if payload.trading_mode is not None:
        update_map.append((RUNTIME_MODE_KEY, payload.trading_mode.value, "当前运行模式"))
    if payload.binance_testnet_api_key:
        update_map.append((BINANCE_TESTNET_API_KEY, payload.binance_testnet_api_key, "Binance Testnet API Key"))
    if payload.binance_testnet_api_secret:
        update_map.append((BINANCE_TESTNET_API_SECRET, payload.binance_testnet_api_secret, "Binance Testnet API Secret"))
    if payload.binance_mainnet_api_key:
        update_map.append((BINANCE_MAINNET_API_KEY, payload.binance_mainnet_api_key, "Binance Mainnet API Key"))
    if payload.binance_mainnet_api_secret:
        update_map.append((BINANCE_MAINNET_API_SECRET, payload.binance_mainnet_api_secret, "Binance Mainnet API Secret"))
    if payload.llm_base_url:
        update_map.append((LLM_BASE_URL, payload.llm_base_url, "LLM base URL"))
    if payload.llm_model:
        update_map.append((LLM_MODEL, payload.llm_model, "LLM model"))
    if payload.llm_api_key:
        update_map.append((LLM_API_KEY, payload.llm_api_key, "LLM API key"))
    if payload.max_position_size_pct is not None:
        update_map.append((MAX_POSITION_SIZE_PCT, payload.max_position_size_pct, "最大持仓比例"))
    if payload.max_daily_loss_pct is not None:
        update_map.append((MAX_DAILY_LOSS_PCT, payload.max_daily_loss_pct, "最大日亏损比例"))
    if payload.max_consecutive_losses is not None:
        update_map.append((MAX_CONSECUTIVE_LOSSES, payload.max_consecutive_losses, "连续亏损熔断笔数"))
    if payload.max_single_risk_pct is not None:
        update_map.append((MAX_SINGLE_RISK_PCT, payload.max_single_risk_pct, "单笔最大风险比例"))

    if not update_map:
        raise ParamsException("No config fields provided")

    for key, value, description in update_map:
        upsert_system_setting(db, key=key, value=value, fernet=fernet, description=description)

    db.commit()
    apply_runtime_settings_refresh(
        db,
        master_key=base_settings.APP_CONFIG_MASTER_KEY,
        default_trading_mode=base_settings.TRADING_MODE,
    )
    return _build_runtime_config_payload(db)
