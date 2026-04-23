"""Event contracts for the AlphaPilot bus (spec §3.3).

All events share a common EventEnvelope for transport. Each payload is its
own Pydantic model with a ClassVar `event_type` string; EVENT_TYPE_REGISTRY
maps the string back to the class for consumer-side deserialization.

V0.1 publishes a subset (marked ★ in spec §3.3 / plan Task 8). All contracts
are defined here regardless of when they start being published — defining
them up front prevents breaking changes later.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Literal

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Envelope (transport wrapper)
# ---------------------------------------------------------------------------

class EventEnvelope(BaseModel):
    """Transport envelope; payload is the serialized form of any _Event subclass."""

    event_id: str  # UUIDv7
    account_id: int = 1
    trading_mode: str = "testnet"
    occurred_at: datetime
    trace_id: str
    schema_version: int = 1
    event_type: str
    payload: dict[str, Any]


# ---------------------------------------------------------------------------
# Base marker for all event payload classes
# ---------------------------------------------------------------------------

class _Event(BaseModel):
    """Marker base. Subclasses override `event_type` ClassVar."""

    event_type: ClassVar[str] = "_unset"


# ---------------------------------------------------------------------------
# market.*
# ---------------------------------------------------------------------------

class CandleClosed(_Event):
    event_type: ClassVar[str] = "candle.closed"
    symbol: str
    timeframe: str
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


# ---------------------------------------------------------------------------
# factor.*
# ---------------------------------------------------------------------------

class IndicatorsComputed(_Event):
    event_type: ClassVar[str] = "indicators.computed"
    symbol: str
    timeframe: str
    open_time: datetime
    indicator_snapshot_id: int


class FactorsUpdated(_Event):
    event_type: ClassVar[str] = "factors.updated"
    symbol: str
    timeframe: str
    open_time: datetime
    factor_snapshot_id: int


class RegimeClassified(_Event):
    event_type: ClassVar[str] = "regime.classified"
    symbol: str
    timeframe: str
    open_time: datetime
    regime: Literal["trending_up", "trending_down", "ranging", "chaotic"]
    confidence: float


# ---------------------------------------------------------------------------
# decision.*
# ---------------------------------------------------------------------------

class ProposalDrafted(_Event):
    event_type: ClassVar[str] = "proposal.drafted"
    proposal_draft_id: int
    symbol: str
    timeframe: str
    template_id: int | None = None


class DecisionProposed(_Event):
    event_type: ClassVar[str] = "decision.proposed"
    decision_id: int
    symbol: str
    timeframe: str
    action: Literal["OPEN_LONG", "CLOSE_LONG", "HOLD"]
    confidence: float
    source: Literal["ai_trader", "program_trader", "shadow", "manual"]
    strategy_mode: str | None = None
    is_fallback: bool = False


class DecisionReviewed(_Event):
    event_type: ClassVar[str] = "decision.reviewed"
    decision_id: int
    review_id: int
    result: Literal["approve", "adjust", "reject"]


class DecisionDegraded(_Event):
    event_type: ClassVar[str] = "decision.degraded"
    decision_id: int
    original_action: str
    modified_action: str
    reason: str


class DecisionRejected(_Event):
    event_type: ClassVar[str] = "decision.rejected"
    decision_id: int
    reason: str


# ---------------------------------------------------------------------------
# order.*
# ---------------------------------------------------------------------------

class OrderSubmitted(_Event):
    event_type: ClassVar[str] = "order.submitted"
    order_id: int
    symbol: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["MARKET", "LIMIT"]
    quantity: float
    price: float | None = None
    trace_id: str


class OrderFilled(_Event):
    event_type: ClassVar[str] = "order.filled"
    order_id: int
    symbol: str
    filled_quantity: float
    avg_fill_price: float


class OrderFailed(_Event):
    event_type: ClassVar[str] = "order.failed"
    order_id: int
    reason: str


# ---------------------------------------------------------------------------
# position.*
# ---------------------------------------------------------------------------

class PositionOpened(_Event):
    event_type: ClassVar[str] = "position.opened"
    position_id: int
    symbol: str
    quantity: float
    entry_price: float
    stop_loss: float
    take_profit: float | None = None


class PositionUpdated(_Event):
    event_type: ClassVar[str] = "position.updated"
    position_id: int
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class PositionClosed(_Event):
    event_type: ClassVar[str] = "position.closed"
    position_id: int
    exit_price: float
    exit_reason: str


# ---------------------------------------------------------------------------
# trade.*
# ---------------------------------------------------------------------------

class TradeClosed(_Event):
    event_type: ClassVar[str] = "trade.closed"
    trade_id: int
    symbol: str
    pnl: float
    pnl_pct: float
    exit_reason: str


# ---------------------------------------------------------------------------
# risk.*
# ---------------------------------------------------------------------------

class RiskEventTriggered(_Event):
    event_type: ClassVar[str] = "risk.event.triggered"
    risk_event_id: int
    event_subtype: str
    severity: Literal["info", "warn", "critical"] = "warn"
    symbol: str | None = None


class CircuitBreakerTriggered(_Event):
    event_type: ClassVar[str] = "circuit_breaker.triggered"
    reason: str


class ManualOverride(_Event):
    event_type: ClassVar[str] = "manual.override"
    operator_user_id: int
    action: str
    target: str
    reason: str | None = None


# ---------------------------------------------------------------------------
# control.* — commands from Control Plane to Execution Core
# ---------------------------------------------------------------------------

class ControlCommand(_Event):
    event_type: ClassVar[str] = "control.command"
    command: Literal[
        "pause_trading", "resume_trading",
        "close_position", "close_all", "unlock_breaker",
    ]
    operator_user_id: int
    target_position_id: int | None = None
    reason: str | None = None


# ---------------------------------------------------------------------------
# learn.* — V0.3+ (defined for forward compat)
# ---------------------------------------------------------------------------

class ParamsCandidateProposed(_Event):
    event_type: ClassVar[str] = "params.candidate.proposed"
    parameter_version_id: int


class ParamsCandidateValidated(_Event):
    event_type: ClassVar[str] = "params.candidate.validated"
    parameter_version_id: int
    validation_summary: dict[str, Any]


class ParamsApplied(_Event):
    event_type: ClassVar[str] = "params.applied"
    parameter_version_id: int


class ParamsRolledBack(_Event):
    event_type: ClassVar[str] = "params.rolled_back"
    parameter_version_id: int
    reason: str


# ---------------------------------------------------------------------------
# ops.* — V0.3+
# ---------------------------------------------------------------------------

class OpsDiagnosis(_Event):
    event_type: ClassVar[str] = "ops.diagnosis"
    diagnosis_id: int
    severity: Literal["info", "warn", "critical"]


class OpsHeartbeat(_Event):
    event_type: ClassVar[str] = "ops.heartbeat"
    service: str
    uptime_seconds: int


# ---------------------------------------------------------------------------
# Registry — consumers use this to parse envelopes back into typed events
# ---------------------------------------------------------------------------

def _all_event_classes() -> list[type[_Event]]:
    return [
        CandleClosed,
        IndicatorsComputed, FactorsUpdated, RegimeClassified,
        ProposalDrafted, DecisionProposed, DecisionReviewed,
        DecisionDegraded, DecisionRejected,
        OrderSubmitted, OrderFilled, OrderFailed,
        PositionOpened, PositionUpdated, PositionClosed,
        TradeClosed,
        RiskEventTriggered, CircuitBreakerTriggered, ManualOverride,
        ControlCommand,
        ParamsCandidateProposed, ParamsCandidateValidated,
        ParamsApplied, ParamsRolledBack,
        OpsDiagnosis, OpsHeartbeat,
    ]


EVENT_TYPE_REGISTRY: dict[str, type[_Event]] = {
    cls.event_type: cls for cls in _all_event_classes()
}
