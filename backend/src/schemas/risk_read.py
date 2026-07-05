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
