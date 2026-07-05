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


class Ticker24h(BaseModel):
    """24h 行情统计 (handoff P2 行情页)。"""

    symbol: str
    last_price: float
    price_change_pct: float  # 24h 涨跌幅小数 (-0.05 = -5%)
    high_24h: float
    low_24h: float
    volume_24h: float  # base asset 量
    quote_volume_24h: float  # USDT 量


class FuturesMetrics(BaseModel):
    """USDT-M 公共行情指标 (装饰性数据; 不可用时字段为 None)。"""

    symbol: str
    mark_price: float | None = None
    index_price: float | None = None
    funding_rate: float | None = None
    next_funding_time: datetime | None = None
    open_interest: float | None = None


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
