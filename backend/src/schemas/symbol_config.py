"""SymbolConfig 域 Schema — /api/admin/symbols 入参。"""
from __future__ import annotations

from pydantic import BaseModel


class SymbolConfigCreate(BaseModel):
    """POST /api/admin/symbols 入参."""
    symbol: str
    base_asset: str
    quote_asset: str = "USDT"
    enabled: bool = True
    timeframe: str = "15m"
    max_position_size_pct: float | None = None
    priority: int = 100
    sort_order: int = 100
    notes: str | None = None


class SymbolConfigUpdate(BaseModel):
    """PATCH /api/admin/symbols/{id} 入参."""
    base_asset: str | None = None
    quote_asset: str | None = None
    enabled: bool | None = None
    timeframe: str | None = None
    max_position_size_pct: float | None = None
    priority: int | None = None
    sort_order: int | None = None
    notes: str | None = None
