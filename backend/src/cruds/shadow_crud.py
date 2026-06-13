"""CRUD for src.models.shadow."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.shadow import ShadowDecision, ShadowEvaluation


class ShadowDecisionCrud(BaseCrud[ShadowDecision]):
    model = ShadowDecision

shadow_decision_crud = ShadowDecisionCrud()

class ShadowEvaluationCrud(BaseCrud[ShadowEvaluation]):
    model = ShadowEvaluation

shadow_evaluation_crud = ShadowEvaluationCrud()
