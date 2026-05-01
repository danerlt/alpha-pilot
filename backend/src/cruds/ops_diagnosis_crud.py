"""CRUD for src.models.ops_diagnosis."""
from __future__ import annotations

from src.models.ops_diagnosis import OpsDiagnosis
from src.cruds.base_crud import BaseCrud


class OpsDiagnosisCrud(BaseCrud[OpsDiagnosis]):
    model = OpsDiagnosis

ops_diagnosis_crud = OpsDiagnosisCrud()
