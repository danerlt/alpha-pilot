"""CRUD for src.models.system_setting."""
from __future__ import annotations

from src.models.system_setting import SystemSetting
from src.cruds.base_crud import BaseCrud


class SystemSettingCrud(BaseCrud[SystemSetting]):
    model = SystemSetting

system_setting_crud = SystemSettingCrud()
