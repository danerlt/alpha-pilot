"""StrategyRouter — V0.1: single-path routing to AI Trader.

Reserved interface for V0.2+ Program Trader / V0.3+ Shadow routing.
Every routing decision writes an audit_logs row so we can trace why a
particular input went to a particular adapter.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy.orm import Session

from src.models.audit_log import AuditLog
from src.strategy.ai_trader.pipeline import PipelineInput
from src.strategy.proposal import DecisionProposal

logger = logging.getLogger(__name__)


class StrategyAdapter(Protocol):
    def run(self, inp: PipelineInput) -> tuple[DecisionProposal, int | None]: ...


class StrategyRouter:
    def __init__(
        self,
        session: Session,
        ai_trader: StrategyAdapter,
        # V0.2+ will add program_trader: StrategyAdapter | None = None
    ):
        self._session = session
        self._ai_trader = ai_trader

    def decide(self, inp: PipelineInput) -> tuple[DecisionProposal, int | None]:
        """V0.1: always AI Trader. Write the routing decision to audit_logs.

        返回 (proposal, decision_id|None) — decision_id 为 None 表示 prompt 阶段就
        提前回退 (无对应 ai_decisions 行)。下游 worker 直接消费, 不再做 id desc 反查。
        """
        route = "ai_trader"
        self._write_audit(inp, route)
        return self._ai_trader.run(inp)

    def _write_audit(self, inp: PipelineInput, route: str) -> None:
        self._session.add(AuditLog(
            account_id=inp.account_id,
            action="strategy_router_decide",
            resource_type="strategy_route",
            resource_id=f"{inp.symbol}:{inp.timeframe}",
            after_json={
                "route": route,
                "regime": inp.regime,
                "has_open_position": inp.open_position is not None,
                "factor_snapshot_id": inp.factor_snapshot_id,
            },
        ))
        self._session.flush()
