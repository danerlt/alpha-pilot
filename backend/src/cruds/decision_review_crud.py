"""CRUD for src.models.decision_review."""
from __future__ import annotations

from src.models.decision_review import DecisionReview
from src.cruds.base_crud import BaseCrud


class DecisionReviewCrud(BaseCrud[DecisionReview]):
    model = DecisionReview

decision_review_crud = DecisionReviewCrud()
