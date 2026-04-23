"""DecisionProposal — the single contract between Strategy Plane and Execution Core.

Every strategy adapter (AI Trader, Program Trader, Shadow) produces one of
these; Execution Guard / Order Executor don't care which source made it.

The Literal unions encode V0.1 invariants:
  - action restricted to long-only + HOLD (no OPEN_SHORT / CLOSE_SHORT)
  - strategy_mode restricted to the six pre-approved modes (spec §4.1)
  - source tagged for audit (ai_trader / program_trader / shadow / manual)

`is_fallback=True` marks proposals that came from the HOLD safety net
(LLM timeout, JSON parse fail, Review reject, etc.) rather than a real
analysis.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DecisionProposal(BaseModel):
    account_id: int
    symbol: str
    timeframe: str
    action: Literal["OPEN_LONG", "CLOSE_LONG", "HOLD"]
    confidence: float = Field(ge=0.0, le=1.0)
    entry_type: Literal["MARKET", "LIMIT"] | None = None
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    position_size_pct: float | None = Field(default=None, ge=0.0, le=1.0)
    strategy_mode: Literal[
        "ai_trend", "ai_breakout", "ai_observation",
        "program_trend", "program_breakout",
    ]
    reasoning: list[str] = Field(default_factory=list)
    risk_note: str | None = None
    # 元信息 — 审计回放必要
    source: Literal["ai_trader", "program_trader", "shadow", "manual"]
    pipeline_version: str = "v0.1"
    prompt_template_id: int | None = None
    llm_model_id: str | None = None
    factor_snapshot_id: int | None = None
    parent_proposal_id: int | None = None  # 若为 Review adjust/reject 的修正版
    is_fallback: bool = False

    @classmethod
    def fallback_hold(
        cls,
        *,
        account_id: int,
        symbol: str,
        timeframe: str,
        reason: str,
        parent_proposal_id: int | None = None,
        factor_snapshot_id: int | None = None,
    ) -> "DecisionProposal":
        """Canonical HOLD for all safety-net paths.

        Record the reason as a single-element reasoning list so the
        decision log surfaces why the pipeline fell back.
        """
        return cls(
            account_id=account_id,
            symbol=symbol,
            timeframe=timeframe,
            action="HOLD",
            confidence=0.0,
            strategy_mode="ai_observation",
            source="ai_trader",
            reasoning=[f"fallback: {reason}"],
            is_fallback=True,
            parent_proposal_id=parent_proposal_id,
            factor_snapshot_id=factor_snapshot_id,
        )
