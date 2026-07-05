"""market 域响应模型 (webapp 架构 B1)。"""
from __future__ import annotations

from pydantic import BaseModel


class KlineRead(BaseModel):
    open_time: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class TickerOut(BaseModel):
    symbol: str
    last_price: float
    price_change_pct: float | None = None
    high_24h: float | None = None
    low_24h: float | None = None
    volume_24h: float | None = None
    quote_volume_24h: float | None = None
    mark_price: float | None = None
    index_price: float | None = None
    funding_rate: float | None = None
    next_funding_time: str | None = None
    open_interest: float | None = None


class MarketSymbolRead(BaseModel):
    symbol: str
    base_asset: str
    last_price: float | None = None
    price_change_pct: float | None = None
    quote_volume_24h: float | None = None
    has_position: bool
    regime: str | None = None
