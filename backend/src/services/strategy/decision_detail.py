"""DecisionDetailService — GET /api/decisions/{id} 聚合 (handoff P1 §3.3)。

聚合: ai_decisions 主行 + features(因子快照+prompt 输入) + decision_reviews
+ 守卫审计(risk_events.decision_id) + 关联 orders / positions。只读, 不 commit。
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.common.exception.errors import DBException
from src.common.response.response_code import ErrorCode
from src.cruds.decision_crud import ai_decision_crud
from src.cruds.decision_review_crud import decision_review_crud
from src.cruds.factor_crud import factor_snapshot_crud
from src.cruds.order_crud import order_crud
from src.cruds.position_crud import position_crud
from src.cruds.risk_event_crud import risk_event_crud


class DecisionDetailService:
    def __init__(self, session: Session):
        self._session = session

    def get_detail(self, decision_id: int, *, trading_mode: str) -> dict:
        d = ai_decision_crud.get_or_none(self._session, decision_id)
        if d is None or d.trading_mode != trading_mode:
            raise DBException(
                error_code=ErrorCode.NOT_FOUND,
                message=f"decision id={decision_id} not found",
            )

        factors = None
        factor_def_versions = None
        if d.factor_snapshot_id is not None:
            snap = factor_snapshot_crud.get_or_none(self._session, d.factor_snapshot_id)
            if snap is not None:
                factors = snap.factors_json
                factor_def_versions = snap.factor_def_versions_json

        reviews = decision_review_crud.find_by_decision_id(self._session, decision_id)
        guard_events = risk_event_crud.find_by_decision_id(self._session, decision_id)
        orders = order_crud.find_by_decision_id(self._session, decision_id)
        positions = position_crud.find_by_decision_id(self._session, decision_id)

        return {
            "id": d.id,
            "symbol": d.symbol,
            "timeframe": d.timeframe,
            "decided_at": d.decided_at.isoformat(),
            "action": d.action,
            "confidence": float(d.confidence) if d.confidence is not None else None,
            "entry_type": d.entry_type,
            "entry_price": float(d.entry_price) if d.entry_price is not None else None,
            "stop_loss": float(d.stop_loss) if d.stop_loss is not None else None,
            "take_profit": float(d.take_profit) if d.take_profit is not None else None,
            "position_size_pct": float(d.position_size_pct) if d.position_size_pct is not None else None,
            "strategy_mode": d.strategy_mode,
            "reasoning": d.reasoning,
            "risk_note": d.risk_note,
            "is_fallback": d.is_fallback,
            "source": d.source,
            "llm_provider": d.llm_provider,
            "llm_model": d.llm_model,
            "tokens_used": d.tokens_used,
            "latency_ms": d.latency_ms,
            "features": {
                "factor_snapshot_id": d.factor_snapshot_id,
                "factors": factors,
                "factor_def_versions": factor_def_versions,
                "prompt_input": d.prompt_input,
            },
            "reviews": [
                {
                    "id": r.id,
                    "reviewer_type": r.reviewer_type,
                    "result": r.result,
                    "adjustments": r.adjustments_json,
                    "notes": r.notes,
                }
                for r in reviews
            ],
            "guard_events": [
                {
                    "id": g.id,
                    "event_type": g.event_type,
                    "description": g.description,
                    "triggered_at": g.triggered_at.isoformat(),
                    "resolved": g.resolved,
                }
                for g in guard_events
            ],
            "orders": [
                {
                    "id": o.id,
                    "side": o.side,
                    "order_type": o.order_type,
                    "status": o.status,
                    "quantity": float(o.quantity) if o.quantity is not None else None,
                    "avg_fill_price": float(o.avg_fill_price) if o.avg_fill_price is not None else None,
                    "trace_id": o.trace_id,
                    "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None,
                    "filled_at": o.filled_at.isoformat() if o.filled_at else None,
                }
                for o in orders
            ],
            "position_ids": [p.id for p in positions],
        }
