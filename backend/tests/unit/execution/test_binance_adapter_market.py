"""BinanceAdapter 行情扩展单测 — 24h ticker + USDT-M 公共指标 (handoff P2)。"""
from __future__ import annotations

from unittest.mock import MagicMock

from src.core.exchange.binance_adapter import BinanceAdapter


def _adapter(mock_client) -> BinanceAdapter:
    return BinanceAdapter(
        api_key="k", api_secret="s", trading_mode="testnet",
        _client_override=mock_client,
    )


def test_get_ticker_24h_maps_fields():
    mc = MagicMock()
    mc.get_ticker.return_value = {
        "symbol": "BTCUSDT",
        "lastPrice": "50000.5",
        "priceChangePercent": "-2.15",
        "highPrice": "51000",
        "lowPrice": "49000",
        "volume": "12345.6",
        "quoteVolume": "617280000",
    }
    t = _adapter(mc).get_ticker_24h("BTCUSDT")
    assert t is not None
    assert t.symbol == "BTCUSDT"
    assert t.last_price == 50000.5
    assert t.price_change_pct == -0.0215  # 百分比转小数
    assert t.high_24h == 51000.0
    assert t.low_24h == 49000.0
    assert t.volume_24h == 12345.6
    assert t.quote_volume_24h == 617280000.0


def test_get_ticker_24h_returns_none_on_error():
    mc = MagicMock()
    mc.get_ticker.side_effect = RuntimeError("boom")
    assert _adapter(mc).get_ticker_24h("BTCUSDT") is None


def test_get_futures_metrics_maps_fields():
    mc = MagicMock()
    mc.futures_mark_price.return_value = {
        "symbol": "BTCUSDT",
        "markPrice": "50010.1",
        "indexPrice": "50009.9",
        "lastFundingRate": "0.0001",
        "nextFundingTime": 1751700000000,
    }
    mc.futures_open_interest.return_value = {"symbol": "BTCUSDT", "openInterest": "88888.8"}
    m = _adapter(mc).get_futures_metrics("BTCUSDT")
    assert m is not None
    assert m.mark_price == 50010.1
    assert m.index_price == 50009.9
    assert m.funding_rate == 0.0001
    assert m.next_funding_time is not None
    assert m.open_interest == 88888.8


def test_get_futures_metrics_returns_none_on_error():
    """USDT-M 公共数据装饰性 — testnet 不可用时静默返 None。"""
    mc = MagicMock()
    mc.futures_mark_price.side_effect = RuntimeError("futures unavailable")
    assert _adapter(mc).get_futures_metrics("BTCUSDT") is None


def test_get_futures_metrics_partial_oi_failure_keeps_mark_price():
    """OI 单独失败时保留 mark/funding 字段, OI 为 None。"""
    mc = MagicMock()
    mc.futures_mark_price.return_value = {
        "symbol": "BTCUSDT", "markPrice": "50010.1", "indexPrice": "50009.9",
        "lastFundingRate": "0.0001", "nextFundingTime": 1751700000000,
    }
    mc.futures_open_interest.side_effect = RuntimeError("oi down")
    m = _adapter(mc).get_futures_metrics("BTCUSDT")
    assert m is not None
    assert m.mark_price == 50010.1
    assert m.open_interest is None


def test_base_adapter_defaults_return_none():
    """抽象基类默认实现返 None — 既有 stub 不需要实现新方法。"""
    from src.core.exchange.adapter import ExchangeAdapter

    class _Minimal(ExchangeAdapter):
        def get_ticker(self, symbol): ...
        def get_klines(self, symbol, timeframe, *, limit=300, end_time=None): ...
        def submit_order(self, request): ...
        def get_order(self, symbol, exchange_order_id): ...
        def cancel_order(self, symbol, exchange_order_id): ...
        def get_balance(self, asset): ...
        @property
        def trading_mode(self):
            return "testnet"

    stub = _Minimal()
    assert stub.get_ticker_24h("BTCUSDT") is None
    assert stub.get_futures_metrics("BTCUSDT") is None
