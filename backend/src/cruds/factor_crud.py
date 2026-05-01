"""CRUD for src.models.factor."""
from __future__ import annotations

from src.models.factor import FactorDefinition, FactorSnapshot, FactorCandidate
from src.cruds.base_crud import BaseCrud


class FactorDefinitionCrud(BaseCrud[FactorDefinition]):
    model = FactorDefinition

factor_definition_crud = FactorDefinitionCrud()

class FactorSnapshotCrud(BaseCrud[FactorSnapshot]):
    model = FactorSnapshot

factor_snapshot_crud = FactorSnapshotCrud()

class FactorCandidateCrud(BaseCrud[FactorCandidate]):
    model = FactorCandidate

factor_candidate_crud = FactorCandidateCrud()
