"""Exchange-agnostic value types used by ExchangeAdapter.

Pydantic models so JSON serialization + validation come for free. These
types are the contract between the business layer and any concrete exchange
implementation; nothing exchange-specific (e.g. Binance symbols, tick sizes)
leaks through.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Kline(BaseModel):
    symbol: str
    timeframe: str
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class Ticker(BaseModel):
    symbol: str
    price: float
    fetched_at: datetime | None = None


class OrderRequest(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["MARKET", "LIMIT"]
    quantity: float
    price: float | None = None  # required for LIMIT
    client_order_id: str | None = None  # trace_id carrier for idempotency


class OrderResult(BaseModel):
    exchange_order_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["MARKET", "LIMIT"]
    status: Literal["NEW", "FILLED", "PARTIALLY_FILLED", "CANCELED", "REJECTED", "EXPIRED"]
    requested_quantity: float
    filled_quantity: float
    avg_fill_price: float | None = None
    client_order_id: str | None = None
    submitted_at: datetime | None = None
    filled_at: datetime | None = None
