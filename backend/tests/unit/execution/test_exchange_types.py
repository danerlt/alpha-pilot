from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.execution.exchange.adapter import ExchangeAdapter
from src.execution.exchange.types import Kline, OrderRequest, OrderResult, Ticker


def test_kline_round_trip():
    k = Kline(
        symbol="BTCUSDT", timeframe="1h",
        open_time=datetime.now(timezone.utc),
        open=100.0, high=110.0, low=95.0, close=105.0, volume=1000.0,
    )
    assert k.symbol == "BTCUSDT"
    data = k.model_dump()
    assert data["close"] == 105.0


def test_ticker_has_price():
    t = Ticker(symbol="BTCUSDT", price=105.5)
    assert t.price == 105.5


def test_order_request_required_fields():
    req = OrderRequest(
        symbol="BTCUSDT", side="BUY", order_type="MARKET", quantity=0.01,
    )
    assert req.quantity == 0.01
    assert req.price is None
    assert req.client_order_id is None


def test_order_request_rejects_invalid_side():
    with pytest.raises(Exception):
        OrderRequest(
            symbol="X", side="INVALID", order_type="MARKET", quantity=1,
        )


def test_order_result_status_literal():
    r = OrderResult(
        exchange_order_id="12345", symbol="BTCUSDT",
        side="BUY", order_type="MARKET",
        status="FILLED",
        requested_quantity=0.01, filled_quantity=0.01, avg_fill_price=100.0,
    )
    assert r.status == "FILLED"


def test_exchange_adapter_is_abstract():
    with pytest.raises(TypeError):
        ExchangeAdapter()  # abstract class, cannot instantiate
