"""CRUD for src.models.report."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.report import DailyReport


class DailyReportCrud(BaseCrud[DailyReport]):
    model = DailyReport

daily_report_crud = DailyReportCrud()
