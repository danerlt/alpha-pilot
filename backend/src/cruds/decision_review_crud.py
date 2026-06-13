"""CRUD for src.models.decision_review."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.decision_review import DecisionReview


class DecisionReviewCrud(BaseCrud[DecisionReview]):
    model = DecisionReview

decision_review_crud = DecisionReviewCrud()
