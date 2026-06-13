"""CRUD for src.models.experience."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.experience import ExperienceRecord


class ExperienceRecordCrud(BaseCrud[ExperienceRecord]):
    model = ExperienceRecord

experience_record_crud = ExperienceRecordCrud()
