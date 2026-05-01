"""RuntimeConfig 域 Schema — /api/config/runtime PATCH/POST 入参。"""
from __future__ import annotations

from pydantic import BaseModel

from src.common.enums import TradingMode


class RuntimeConfigUpdate(BaseModel):
    """POST /api/config/runtime 入参 (admin 在线改运行时配置)."""
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
