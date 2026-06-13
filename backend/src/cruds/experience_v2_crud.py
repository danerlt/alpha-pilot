"""CRUD for src.models.experience_v2."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.experience_v2 import ExperienceSummary, ExperienceV2


class ExperienceV2Crud(BaseCrud[ExperienceV2]):
    model = ExperienceV2

experience_v2_crud = ExperienceV2Crud()

class ExperienceSummaryCrud(BaseCrud[ExperienceSummary]):
    model = ExperienceSummary

experience_summary_crud = ExperienceSummaryCrud()
