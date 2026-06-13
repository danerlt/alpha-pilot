"""AITraderPipeline — orchestrates Prompt → Retrieval → Decision → Review.

Given a PipelineInput, returns exactly one (DecisionProposal, decision_id|None)
tuple. decision_id 直接来自 DecisionSolver 写入的 ai_decisions.id, 让下游
worker 不需要再做 `order_by(id desc)` 反查 (修 Plan5 codereview I4)。

decision_id 为 None 的语义：尚未走到 Solver 阶段就回退了 (e.g. prompt 模板缺失
/ 模板渲染异常), 此时不存在对应 ai_decisions 行。

任何阶段失败仍走 DecisionProposal.fallback_hold; pipeline 本身永不抛异常。

Stage summary:
  1. ExperienceRetriever.top_k  → recent summaries for prompt context
  2. PromptComposer.compose     → PromptBundle (+ proposal_drafts row)
  3. DecisionSolver.solve       → DecisionProposal + decision_id (+ ai_decisions row)
  4. ReviewCritic.review        → approve / adjust / reject
     - approve → return solver proposal
     - adjust  → return clone of proposal with adjustments applied
     - reject  → return fallback_hold, parent_proposal_id points to solver's ai_decisions
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.services.insight.experience.retriever import ExperienceRetriever, ExperienceSummary
from src.services.strategy.decision_solver import DecisionSolver
from src.services.strategy.prompt_composer import (
    PromptComposer,
    PromptContext,
    PromptTemplateNotFound,
)
from src.services.strategy.proposal import DecisionProposal
from src.services.strategy.review_critic import ReviewCritic

logger = logging.getLogger(__name__)


@dataclass
class PipelineInput:
    account_id: int
    trading_mode: str
    symbol: str
    timeframe: str
    current_price: float
    indicators: dict[str, float | None]
    factors: dict[str, float]
    regime: str
    open_position: dict | None
    account_snapshot: dict
    factor_snapshot_id: int | None
    atr: float  # needed by ReviewCritic
    experience_limit: int = 5


class AITraderPipeline:
    """Usable as a StrategyAdapter — `run(inp)` returns
    `(DecisionProposal, decision_id | None)`.

    decision_id 是 ai_decisions.id (Solver 阶段写入), 用于让 OrderExecutor 关联
    持仓和决策, 不再需要 worker 做反向查询。
    """

    def __init__(
        self,
        session: Session,
        *,
        composer: PromptComposer,
        retriever: ExperienceRetriever,
        solver: DecisionSolver,
        critic: ReviewCritic,
    ):
        self._session = session
        self._composer = composer
        self._retriever = retriever
        self._solver = solver
        self._critic = critic

    def run(self, inp: PipelineInput) -> tuple[DecisionProposal, int | None]:
        # Stage 1: experience retrieval (cheap, non-fatal if it errors).
        try:
            recent: list[ExperienceSummary] = self._retriever.top_k(
                account_id=inp.account_id,
                symbol=inp.symbol,
                regime=inp.regime,
                limit=inp.experience_limit,
            )
        except Exception:
            logger.exception("experience retrieval failed; proceeding with empty context")
            recent = []

        # Stage 2: prompt composition.
        try:
            bundle = self._composer.compose(PromptContext(
                account_id=inp.account_id,
                trading_mode=inp.trading_mode,
                symbol=inp.symbol,
                timeframe=inp.timeframe,
                current_price=inp.current_price,
                indicators=inp.indicators,
                factors=inp.factors,
                regime=inp.regime,
                open_position=inp.open_position,
                account_snapshot=inp.account_snapshot,
                recent_experience=[e.__dict__ for e in recent],
            ))
        except PromptTemplateNotFound as e:
            return DecisionProposal.fallback_hold(
                account_id=inp.account_id, symbol=inp.symbol, timeframe=inp.timeframe,
                reason=f"prompt_template_missing:{e}",
                factor_snapshot_id=inp.factor_snapshot_id,
            ), None
        except Exception as e:  # noqa: BLE001
            logger.exception("prompt composition failed")
            return DecisionProposal.fallback_hold(
                account_id=inp.account_id, symbol=inp.symbol, timeframe=inp.timeframe,
                reason=f"prompt_compose_error:{e}",
                factor_snapshot_id=inp.factor_snapshot_id,
            ), None

        # Stage 3: solver (already handles its own failures and writes ai_decisions).
        proposal, decision_id = self._solver.solve(
            prompt_bundle=bundle,
            account_id=inp.account_id,
            trading_mode=inp.trading_mode,
            symbol=inp.symbol,
            timeframe=inp.timeframe,
            factor_snapshot_id=inp.factor_snapshot_id,
        )

        # If the solver already fell back, skip review — HOLD is HOLD.
        if proposal.is_fallback:
            return proposal, decision_id

        # Stage 4: review.
        try:
            review = self._critic.review(
                proposal=proposal,
                decision_id=decision_id,
                regime=inp.regime,
                atr=inp.atr,
                recent_experience=recent,
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("review failed; falling back to HOLD")
            return DecisionProposal.fallback_hold(
                account_id=inp.account_id, symbol=inp.symbol, timeframe=inp.timeframe,
                reason=f"review_error:{e}",
                parent_proposal_id=decision_id,
                factor_snapshot_id=inp.factor_snapshot_id,
            ), decision_id

        if review.result == "approve":
            return proposal, decision_id

        if review.result == "adjust" and review.adjustments:
            # Apply bounded adjustments (V0.1 only ever touches take_profit).
            updated = proposal.model_copy(update=review.adjustments)
            updated.risk_note = (proposal.risk_note or "") + f" | review_adjust:{review.notes}"
            updated.parent_proposal_id = decision_id
            return updated, decision_id

        # Reject → fallback HOLD.
        return DecisionProposal.fallback_hold(
            account_id=inp.account_id, symbol=inp.symbol, timeframe=inp.timeframe,
            reason=f"review_reject:{review.notes}",
            parent_proposal_id=decision_id,
            factor_snapshot_id=inp.factor_snapshot_id,
        ), decision_id
