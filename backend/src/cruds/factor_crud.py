"""CRUD for src.models.factor."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.base_crud import BaseCrud
from src.models.factor import FactorCandidate, FactorDefinition, FactorSnapshot


class FactorDefinitionCrud(BaseCrud[FactorDefinition]):
    model = FactorDefinition

factor_definition_crud = FactorDefinitionCrud()

class FactorSnapshotCrud(BaseCrud[FactorSnapshot]):
    model = FactorSnapshot

    def find_latest_by_symbol(
        self, session: Session, *, trading_mode: str, symbol: str, account_id: int = 1,
    ) -> FactorSnapshot | None:
        return session.execute(
            select(FactorSnapshot).where(
                FactorSnapshot.account_id == account_id,
                FactorSnapshot.trading_mode == trading_mode,
                FactorSnapshot.symbol == symbol,
            ).order_by(FactorSnapshot.open_time.desc()).limit(1)
        ).scalars().first()

factor_snapshot_crud = FactorSnapshotCrud()

class FactorCandidateCrud(BaseCrud[FactorCandidate]):
    model = FactorCandidate

factor_candidate_crud = FactorCandidateCrud()
