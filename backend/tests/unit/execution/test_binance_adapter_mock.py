"""Binance adapter with python-binance client mocked; verifies mapping logic."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from binance.exceptions import BinanceAPIException

from src.core.exchange.binance_adapter import BinanceAdapter
from src.core.exchange.retry import (
    ExchangeTemporarilyUnavailable,
    PermanentExchangeError,
)
from src.core.exchange.types import OrderRequest


def _mk_binance_exception(status_code: int) -> BinanceAPIException:
    """Construct BinanceAPIException without going through its JSON parser.

    The __init__ tries to parse `text` as JSON; we bypass via __new__ and set
    only the fields the adapter's error mapper actually inspects. Avoids
    brittleness across python-binance versions.
    """
    exc = BinanceAPIException.__new__(BinanceAPIException)
    exc.status_code = status_code
    exc.code = 0
    exc.message = f"mock {status_code}"
    exc.response = MagicMock()
    exc.args = (f"{status_code} mock error",)
    return exc


def _adapter_with_mock_client(mock_client):
    return BinanceAdapter(
        api_key="k", api_secret="s", trading_mode="testnet",
        _client_override=mock_client,
    )


def test_get_ticker_parses_price():
    mc = MagicMock()
    mc.get_symbol_ticker.return_value = {"symbol": "BTCUSDT", "price": "105.5"}
    a = _adapter_with_mock_client(mc)
    t = a.get_ticker("BTCUSDT")
    assert t.price == 105.5
    assert t.symbol == "BTCUSDT"


def test_submit_order_returns_order_result():
    mc = MagicMock()
    mc.create_order.return_value = {
        "orderId": 12345,
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "status": "FILLED",
        "origQty": "0.01",
        "executedQty": "0.01",
        "cummulativeQuoteQty": "1055",
        "clientOrderId": "trace123",
    }
    a = _adapter_with_mock_client(mc)
    res = a.submit_order(OrderRequest(
        symbol="BTCUSDT", side="BUY", order_type="MARKET",
        quantity=0.01, client_order_id="trace123",
    ))
    assert res.exchange_order_id == "12345"
    assert res.status == "FILLED"
    assert res.avg_fill_price == 1055 / 0.01
    assert res.client_order_id == "trace123"


def test_5xx_maps_to_transient():
    mc = MagicMock()
    mc.get_symbol_ticker.side_effect = _mk_binance_exception(500)
    a = _adapter_with_mock_client(mc)
    with pytest.raises(ExchangeTemporarilyUnavailable):
        a.get_ticker("BTCUSDT")


def test_4xx_maps_to_permanent():
    mc = MagicMock()
    mc.get_symbol_ticker.side_effect = _mk_binance_exception(400)
    a = _adapter_with_mock_client(mc)
    with pytest.raises(PermanentExchangeError):
        a.get_ticker("BTCUSDT")


def test_429_maps_to_transient():
    mc = MagicMock()
    mc.get_symbol_ticker.side_effect = _mk_binance_exception(429)
    a = _adapter_with_mock_client(mc)
    with pytest.raises(ExchangeTemporarilyUnavailable):
        a.get_ticker("BTCUSDT")


def test_trading_mode_property():
    mc = MagicMock()
    a = BinanceAdapter(
        api_key="k", api_secret="s", trading_mode="mainnet",
        _client_override=mc,
    )
    assert a.trading_mode == "mainnet"


def test_klines_parse_binance_raw_rows():
    mc = MagicMock()
    # Binance returns klines as list of lists: [open_time_ms, open, high, low, close, volume, ...]
    mc.get_klines.return_value = [
        [1714176000000, "100.0", "110.0", "95.0", "105.0", "1000.0", 0, "0", 0, "0", "0", "0"],
        [1714179600000, "105.0", "108.0", "103.0", "107.0", "800.0", 0, "0", 0, "0", "0", "0"],
    ]
    a = _adapter_with_mock_client(mc)
    klines = a.get_klines("BTCUSDT", "1h", limit=2)
    assert len(klines) == 2
    assert klines[0].close == 105.0
    assert klines[1].volume == 800.0
