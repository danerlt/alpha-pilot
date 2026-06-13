"""CRUD for src.models.system_setting."""
from __future__ import annotations

from src.cruds.base_crud import BaseCrud
from src.models.system_setting import SystemSetting


class SystemSettingCrud(BaseCrud[SystemSetting]):
    model = SystemSetting

system_setting_crud = SystemSettingCrud()
