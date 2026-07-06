"""strategy 域响应模型 (webapp 架构 B1)。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DecisionRead(BaseModel):
    id: int
    symbol: str
    timeframe: str
    action: str
    guard_verdict: str | None = None  # PASS/REJECT/DEGRADE (联调缺口#1)
    confidence: float | None = None
    entry_price: float | None = None  # 联调缺口#1 顺带: 决策卡头部五格
    stop_loss: float | None = None
    take_profit: float | None = None
    position_size_pct: float | None = None
    strategy_mode: str | None = None
    reasoning: list[Any] | None = None
    risk_note: str | None = None
    is_fallback: bool
    decided_at: str


class DecisionFeaturesOut(BaseModel):
    factor_snapshot_id: int | None = None
    factors: dict[str, Any] | None = None
    factor_def_versions: dict[str, Any] | None = None
    prompt_input: dict[str, Any] | None = None


class DecisionReviewRead(BaseModel):
    id: int
    reviewer_type: str
    result: str
    adjustments: dict[str, Any] | None = None
    notes: str | None = None


class DecisionGuardEventRead(BaseModel):
    id: int
    event_type: str
    description: str
    triggered_at: str
    resolved: bool


class DecisionOrderRead(BaseModel):
    id: int
    side: str
    order_type: str
    status: str
    quantity: float | None = None
    avg_fill_price: float | None = None
    trace_id: str
    submitted_at: str | None = None
    filled_at: str | None = None


class DecisionDetailOut(BaseModel):
    id: int
    symbol: str
    timeframe: str
    decided_at: str
    action: str
    confidence: float | None = None
    entry_type: str | None = None
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    position_size_pct: float | None = None
    strategy_mode: str | None = None
    reasoning: list[Any] | None = None
    risk_note: str | None = None
    is_fallback: bool
    source: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    tokens_used: int | None = None
    latency_ms: int | None = None
    features: DecisionFeaturesOut
    reviews: list[DecisionReviewRead]
    guard_events: list[DecisionGuardEventRead]
    orders: list[DecisionOrderRead]
    position_ids: list[int]
