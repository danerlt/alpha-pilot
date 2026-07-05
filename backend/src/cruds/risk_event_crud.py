"""CRUD for src.models.risk_event."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.risk_event import RiskEvent


class RiskEventCrud(BaseCrud[RiskEvent]):
    model = RiskEvent

    def find_by_decision_id(self, session: Session, decision_id: int) -> list[RiskEvent]:
        return list(session.execute(
            select(RiskEvent)
            .where(RiskEvent.decision_id == decision_id)
            .order_by(RiskEvent.id)
        ).scalars())

risk_event_crud = RiskEventCrud()
