"""Live integration test against Binance Testnet.

Skipped automatically if BINANCE_API_KEY / BINANCE_API_SECRET aren't set to
non-placeholder values. In CI this test only runs when real testnet creds
are injected.
"""
from __future__ import annotations

import os

import pytest

from src.execution.exchange.binance_adapter import BinanceAdapter


def _skip_if_no_credentials():
    key = os.environ.get("BINANCE_API_KEY", "")
    secret = os.environ.get("BINANCE_API_SECRET", "")
    if not key or key.startswith("test-") or not secret or secret.startswith("test-"):
        pytest.skip("no real Binance testnet credentials in env")


def test_live_get_ticker():
    _skip_if_no_credentials()
    a = BinanceAdapter(
        api_key=os.environ["BINANCE_API_KEY"],
        api_secret=os.environ["BINANCE_API_SECRET"],
        trading_mode="testnet",
    )
    t = a.get_ticker("BTCUSDT")
    assert t.symbol == "BTCUSDT"
    assert t.price > 0


def test_live_get_klines():
    _skip_if_no_credentials()
    a = BinanceAdapter(
        api_key=os.environ["BINANCE_API_KEY"],
        api_secret=os.environ["BINANCE_API_SECRET"],
        trading_mode="testnet",
    )
    ks = a.get_klines("BTCUSDT", "1h", limit=5)
    assert len(ks) == 5
    for k in ks:
        assert k.close > 0
