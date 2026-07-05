"""CRUD for src.models.agent_pending_action."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.agent_pending_action import AgentPendingAction


class AgentPendingActionCrud(BaseCrud[AgentPendingAction]):
    model = AgentPendingAction

    def mark_confirmed(
        self, session: Session, id: int, *, confirmed_by: int,
    ) -> AgentPendingAction:
        obj = self.get(session, id)
        obj.status = "CONFIRMED"
        obj.confirmed_by = confirmed_by
        obj.confirmed_at = datetime.now(tz=timezone.utc)
        session.flush()
        return obj

    def find_latest(self, session: Session, *, limit: int = 20) -> list[AgentPendingAction]:
        return list(session.execute(
            select(AgentPendingAction)
            .order_by(AgentPendingAction.id.desc())
            .limit(limit)
        ).scalars())

agent_pending_action_crud = AgentPendingActionCrud()
