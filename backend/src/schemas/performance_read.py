"""performance 域响应模型 (handoff 3.8)。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PerformanceSummaryOut(BaseModel):
    range_days: int
    net_return_pct: float | None = None
    hodl_return_pct: float | None = None
    vs_hodl_pct: float | None = None
    sharpe: float | None = None
    sortino: float | None = None
    max_drawdown_pct: float | None = None
    win_rate: float | None = None
    profit_factor: float | None = None
    trades: int
    net_pnl: float
    today_trades: int
    avg_holding_seconds: int | None = None
    week_pnl: float
    month_pnl: float
    curve: list[dict[str, Any]]


class MonthlyPnlRead(BaseModel):
    month: str
    pnl: float
    trades: int


class AttributionBucketRead(BaseModel):
    key: str
    trades: int
    net_pnl: float
    win_rate: float | None = None
