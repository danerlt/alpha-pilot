"""ReviewCritic — rule-based V0.1 second-pass validator.

Reviews a DecisionProposal that's already cleared DecisionSolver and
checks it against four invariants:

  1. SL/TP sanity: |entry - sl| must be in [sl_atr_min_mult, sl_atr_max_mult] * ATR
  2. R/R ratio:    |tp - entry| / |entry - sl| >= min_rr_ratio
  3. Regime fit:   trending_down + OPEN_LONG → reject (catching a knife)
  4. Experience alarm (soft): 3 latest same-mode trades all negative → warn only (V0.1)

Verdicts:
  - approve: no changes, keep as-is
  - adjust:  bounded adjustment (V0.1 only auto-fixes TP when R/R below threshold)
  - reject:  return reason; pipeline falls back to HOLD

Every review persists a decision_reviews row (reviewer_type="rule") so the
audit record is complete.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy.orm import Session

from src.insight.experience.retriever import ExperienceSummary
from src.shared.models.decision_review import DecisionReview
from src.strategy.proposal import DecisionProposal


@dataclass
class ReviewResult:
    result: Literal["approve", "adjust", "reject"]
    adjustments: dict | None = None  # when result == adjust
    notes: str = ""


class ReviewCritic:
    def __init__(
        self,
        session: Session,
        *,
        min_rr_ratio: float = 1.5,
        sl_atr_min_mult: float = 0.5,
        sl_atr_max_mult: float = 5.0,
    ):
        self._session = session
        self._min_rr = min_rr_ratio
        self._sl_min = sl_atr_min_mult
        self._sl_max = sl_atr_max_mult

    def review(
        self,
        *,
        proposal: DecisionProposal,
        decision_id: int,
        regime: str,
        atr: float,
        recent_experience: list[ExperienceSummary],
    ) -> ReviewResult:
        """Return a verdict + persist a decision_reviews row. Never raises."""
        # HOLD proposals are auto-approved — no risk to vet.
        if proposal.action == "HOLD":
            return self._persist(decision_id, result="approve", notes="hold_auto_approved")

        # Need entry + sl for the remaining checks; treat missing as reject.
        entry = proposal.entry_price
        sl = proposal.stop_loss
        if entry is None or sl is None or atr <= 0:
            return self._persist(
                decision_id, result="reject",
                notes="missing_entry_or_sl_or_atr",
            )

        # 1. Regime fit — catch a knife check.
        if regime == "trending_down" and proposal.action == "OPEN_LONG":
            return self._persist(
                decision_id, result="reject",
                notes="regime_fit:open_long_in_trending_down",
            )

        # 2. SL / ATR distance.
        sl_distance = abs(entry - sl)
        min_distance = self._sl_min * atr
        max_distance = self._sl_max * atr
        if not (min_distance <= sl_distance <= max_distance):
            return self._persist(
                decision_id, result="reject",
                notes=f"sl_distance:{sl_distance:.6f} outside [{min_distance:.6f}, {max_distance:.6f}]",
            )

        # 3. R/R ratio. If TP provided but R/R below threshold, adjust TP to
        # exactly min_rr away from entry in the profit direction.
        tp = proposal.take_profit
        if tp is None:
            # V0.1: require TP for OPEN_LONG; reject if missing.
            if proposal.action == "OPEN_LONG":
                return self._persist(
                    decision_id, result="reject",
                    notes="missing_take_profit_on_open_long",
                )
        else:
            reward = abs(tp - entry)
            if reward <= 0 or reward / sl_distance < self._min_rr:
                fixed_tp = entry + sl_distance * self._min_rr if proposal.action == "OPEN_LONG" else entry - sl_distance * self._min_rr
                return self._persist(
                    decision_id,
                    result="adjust",
                    adjustments={"take_profit": fixed_tp},
                    notes=f"rr_below_{self._min_rr}:adjusted_tp_to_{fixed_tp:.6f}",
                )

        # 4. Experience alarm — soft in V0.1.
        same_mode_recent = [
            e for e in recent_experience[:3]
            if e.strategy_mode == proposal.strategy_mode and e.pnl_pct is not None
        ]
        if len(same_mode_recent) == 3 and all(e.pnl_pct < 0 for e in same_mode_recent):
            return self._persist(
                decision_id,
                result="approve",
                notes="experience_alarm:last_3_same_mode_negative",
            )

        return self._persist(decision_id, result="approve", notes="all_checks_passed")

    def _persist(
        self,
        decision_id: int,
        *,
        result: Literal["approve", "adjust", "reject"],
        adjustments: dict | None = None,
        notes: str = "",
    ) -> ReviewResult:
        row = DecisionReview(
            decision_id=decision_id,
            reviewer_type="rule",
            result=result,
            adjustments_json=adjustments,
            notes=notes,
        )
        self._session.add(row)
        self._session.flush()
        return ReviewResult(result=result, adjustments=adjustments, notes=notes)
