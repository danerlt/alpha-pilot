"""CRUD for src.models.lab_candidate."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.lab_candidate import LabCandidate


class LabCandidateCrud(BaseCrud[LabCandidate]):
    model = LabCandidate

    def find_by_stage(
        self, session: Session, stages: list[str], *, trading_mode: str,
    ) -> list[LabCandidate]:
        return list(session.execute(
            select(LabCandidate).where(
                LabCandidate.stage.in_(stages),
                LabCandidate.trading_mode == trading_mode,
            ).order_by(LabCandidate.id.desc())
        ).scalars())

    def find_all(self, session: Session, *, trading_mode: str, limit: int = 100) -> list[LabCandidate]:
        return list(session.execute(
            select(LabCandidate).where(
                LabCandidate.trading_mode == trading_mode,
            ).order_by(LabCandidate.id.desc()).limit(limit)
        ).scalars())

lab_candidate_crud = LabCandidateCrud()
