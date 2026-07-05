"""CRUD for src.models.risk_event."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.risk_event import RiskEvent


class RiskEventCrud(BaseCrud[RiskEvent]):
    model = RiskEvent

    def find_guard_verdicts(self, session: Session, decision_ids: list[int]) -> dict[int, str]:
        """批量取每个 decision 最新 GUARD_* 事件 → verdict (PASS/REJECT/DEGRADE)。"""
        if not decision_ids:
            return {}
        rows = session.execute(
            select(RiskEvent).where(
                RiskEvent.decision_id.in_(decision_ids),
                RiskEvent.event_type.like("GUARD_%"),
            ).order_by(RiskEvent.id)
        ).scalars()
        out: dict[int, str] = {}
        for r in rows:  # id 升序, 后写覆盖 → 每个 decision 留最新
            out[r.decision_id] = r.event_type.removeprefix("GUARD_")
        return out

    def find_by_decision_id(self, session: Session, decision_id: int) -> list[RiskEvent]:
        return list(session.execute(
            select(RiskEvent)
            .where(RiskEvent.decision_id == decision_id)
            .order_by(RiskEvent.id)
        ).scalars())

risk_event_crud = RiskEventCrud()
