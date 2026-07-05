"""risk 域响应模型 (webapp 架构 B1)。"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class RiskEventRead(BaseModel):
    id: int
    event_type: str
    symbol: str | None = None
    description: str
    resolved: bool
    triggered_at: str
    resolved_at: str | None = None


class RiskStateOut(BaseModel):
    state: Literal["OK", "WARN", "HALTED"]
    day_loss_pct: float
    positions_pct: float
    regime: str | None = None


class RiskLimitsOut(BaseModel):
    """硬风控阈值只读视图 (联调缺口#7); 值为 runtime 覆盖后的生效值。"""

    max_position_size_pct: float
    max_daily_loss_pct: float
    max_consecutive_losses: int
    max_single_risk_pct: float
    min_rr_ratio: float | None = None
    sl_atr_min_mult: float | None = None
    sl_atr_max_mult: float | None = None
