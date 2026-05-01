"""CRUD for src.models.shadow."""
from __future__ import annotations

from src.models.shadow import ShadowDecision, ShadowEvaluation
from src.cruds.base_crud import BaseCrud


class ShadowDecisionCrud(BaseCrud[ShadowDecision]):
    model = ShadowDecision

shadow_decision_crud = ShadowDecisionCrud()

class ShadowEvaluationCrud(BaseCrud[ShadowEvaluation]):
    model = ShadowEvaluation

shadow_evaluation_crud = ShadowEvaluationCrud()
