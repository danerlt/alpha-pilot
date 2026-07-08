"""execution 域响应模型 (webapp 架构 B1: data 必须有具体模型, 否则前端生成 unknown)。

时间字段统一 isoformat 字符串 (与现有手工序列化一致, 避免双重序列化)。
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PositionRead(BaseModel):
    id: int
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float | None = None
    unrealized_pnl: float
    unrealized_pnl_pct: float
    opened_at: str
    strategy_mode: str | None = None  # 联调缺口#4: 决策反查
    position_pct: float | None = None  # 联调缺口#4: 仓位市值/总权益


class TradeRead(BaseModel):
    id: int
    symbol: str
    quantity: float
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    exit_reason: str
    strategy_mode: str | None = None
    regime: str | None = None
    opened_at: str
    closed_at: str
    holding_seconds: int | None = None


class AccountSnapshotRead(BaseModel):
    """无快照时只有 message 字段 (历史行为保留), 其余为 None。"""

    total_balance_usdt: float | None = None
    available_balance_usdt: float | None = None
    unrealized_pnl: float | None = None
    daily_pnl: float | None = None
    daily_pnl_pct: float | None = None
    snapshot_at: str | None = None
    message: str | None = None


class SltpOut(BaseModel):
    position_id: int
    stop_loss: float | None = None
    take_profit: float | None = None


class GuardCheckItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    check: str
    pass_: bool = Field(alias="pass")
    note: str
    category: str  # physical | breaker | soft (服务端权威分类, 前端据此判定按钮态)


class PrecheckOut(BaseModel):
    verdict: str
    halted: bool
    checks: list[GuardCheckItem]
    context: dict


class OrderPlacedOut(BaseModel):
    order_id: int | None = None
    trace_id: str | None = None
    status: str | None = None
    position_id: int | None = None
    trade_id: int | None = None


class EquityPointRead(BaseModel):
    """权益曲线单点 (联调缺口#2)。"""

    ts: str
    equity: float


class OrderListItemRead(BaseModel):
    """订单簿表行 (联调缺口#3)。"""

    id: int
    symbol: str
    side: str
    order_type: str
    status: str
    quantity: float
    price: float | None = None
    avg_fill_price: float | None = None
    trace_id: str
    position_id: int | None = None
    ai_decision_id: int | None = None
    submitted_at: str
    filled_at: str | None = None
