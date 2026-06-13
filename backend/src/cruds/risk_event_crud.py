"""CRUD for src.models.risk_event."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.risk_event import RiskEvent


class RiskEventCrud(BaseCrud[RiskEvent]):
    model = RiskEvent

risk_event_crud = RiskEventCrud()
