"""CRUD for src.models.experience."""
from __future__ import annotations

from src.models.experience import ExperienceRecord
from src.cruds.base_crud import BaseCrud


class ExperienceRecordCrud(BaseCrud[ExperienceRecord]):
    model = ExperienceRecord

experience_record_crud = ExperienceRecordCrud()
