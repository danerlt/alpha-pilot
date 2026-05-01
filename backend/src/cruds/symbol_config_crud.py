"""CRUD for src.models.symbol_config."""
from __future__ import annotations

from src.models.symbol_config import SymbolConfig
from src.cruds.base_crud import BaseCrud


class SymbolConfigCrud(BaseCrud[SymbolConfig]):
    model = SymbolConfig

symbol_config_crud = SymbolConfigCrud()
