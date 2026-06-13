"""CRUD for src.models.decision."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.decision import AIDecision


class AIDecisionCrud(BaseCrud[AIDecision]):
    model = AIDecision

ai_decision_crud = AIDecisionCrud()
