"""CRUD for src.models.report."""
from __future__ import annotations

from src.models.report import DailyReport
from src.cruds.base_crud import BaseCrud


class DailyReportCrud(BaseCrud[DailyReport]):
    model = DailyReport

daily_report_crud = DailyReportCrud()
