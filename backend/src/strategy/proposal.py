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

import math
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class DecisionProposal(BaseModel):
    account_id: int
    symbol: str
    timeframe: str
    action: Literal["OPEN_LONG", "CLOSE_LONG", "HOLD"]
    confidence: float = Field(ge=0.0, le=1.0)
    entry_type: Literal["MARKET", "LIMIT"] | None = None
    # 价格 / SL / TP 必须 > 0 (post-Plan5 安全审计 C6: 防 NaN/Inf/<=0 绕过 Guard)
    entry_price: float | None = Field(default=None, gt=0.0)
    stop_loss: float | None = Field(default=None, gt=0.0)
    take_profit: float | None = Field(default=None, gt=0.0)
    position_size_pct: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("entry_price", "stop_loss", "take_profit", "position_size_pct", "confidence")
    @classmethod
    def _reject_non_finite(cls, v):
        """Pydantic 的 ge/gt/le 约束会接受 NaN (NaN 在所有比较中都返回 False), 必须显式拒.

        触发场景: LLM 返回 NaN/Infinity (Python 标准 json.loads 接受这些
        非标准 JSON 扩展), Pydantic 没有 finite 约束就放行 → ExecutionGuard
        的 risk_pct, sl_distance 等计算全部 NaN → 所有规则被绕过.
        """
        if v is None:
            return v
        if not math.isfinite(v):
            raise ValueError(f"value must be finite (got {v!r})")
        return v
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
