"""CRUD for src.models.decision."""
from __future__ import annotations

from src.models.decision import AIDecision
from src.cruds.base_crud import BaseCrud


class AIDecisionCrud(BaseCrud[AIDecision]):
    model = AIDecision

ai_decision_crud = AIDecisionCrud()
