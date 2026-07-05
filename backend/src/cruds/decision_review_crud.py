"""CRUD for src.models.decision_review."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.decision_review import DecisionReview


class DecisionReviewCrud(BaseCrud[DecisionReview]):
    model = DecisionReview

    def find_by_decision_id(self, session: Session, decision_id: int) -> list[DecisionReview]:
        return list(session.execute(
            select(DecisionReview)
            .where(DecisionReview.decision_id == decision_id)
            .order_by(DecisionReview.id)
        ).scalars())

decision_review_crud = DecisionReviewCrud()
