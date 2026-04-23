"""Binance REST adapter on top of python-binance.

testnet/mainnet selection via constructor; the business layer never sees the
distinction.

Every REST call passes through:
  1. RateLimiter.acquire (token bucket, Binance weight limit 1200/min)
  2. @with_retry decorator (exponential backoff for 5xx / 429 / timeout)

BinanceAPIException is mapped to our error hierarchy:
  - status 5xx, 429, or BinanceRequestException → ExchangeTemporarilyUnavailable
  - other 4xx → PermanentExchangeError
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

from src.execution.exchange.adapter import ExchangeAdapter
from src.execution.exchange.rate_limiter import RateLimiter
from src.execution.exchange.retry import (
    ExchangeTemporarilyUnavailable,
    PermanentExchangeError,
    with_retry,
)
from src.execution.exchange.types import Kline, OrderRequest, OrderResult, Ticker

# python-binance interval constants for the timeframes V0.1 uses.
_TIMEFRAME_MAP = {
    "1m": Client.KLINE_INTERVAL_1MINUTE,
    "5m": Client.KLINE_INTERVAL_5MINUTE,
    "15m": Client.KLINE_INTERVAL_15MINUTE,
    "1h": Client.KLINE_INTERVAL_1HOUR,
    "4h": Client.KLINE_INTERVAL_4HOUR,
    "1d": Client.KLINE_INTERVAL_1DAY,
}


def _map_binance_error(exc: Exception) -> Exception:
    if isinstance(exc, BinanceRequestException):
        return ExchangeTemporarilyUnavailable(str(exc))
    if isinstance(exc, BinanceAPIException):
        status = getattr(exc, "status_code", 0) or 0
        if status >= 500 or status == 429:
            return ExchangeTemporarilyUnavailable(f"{status}: {exc}")
        return PermanentExchangeError(f"{status}: {exc}")
    return exc


class BinanceAdapter(ExchangeAdapter):
    def __init__(
        self,
        *,
        api_key: str,
        api_secret: str,
        trading_mode: Literal["testnet", "mainnet"],
        _client_override=None,  # test hook — do not use outside unit tests
    ):
        self._trading_mode = trading_mode
        testnet = trading_mode == "testnet"
        self._client = _client_override or Client(api_key, api_secret, testnet=testnet)
        # Binance weight limit: 1200/min → refill 20/s.
        self._limiter = RateLimiter(capacity=1200, refill_per_second=20)

    @property
    def trading_mode(self) -> Literal["testnet", "mainnet"]:
        return self._trading_mode

    # --------------------------------------------------------------
    # Market data
    # --------------------------------------------------------------

    @with_retry(retries=3, base_delay=0.5, max_delay=8.0)
    def get_ticker(self, symbol: str) -> Ticker:
        self._limiter.acquire(1)
        try:
            raw = self._client.get_symbol_ticker(symbol=symbol)
        except Exception as e:
            raise _map_binance_error(e) from e
        return Ticker(
            symbol=raw["symbol"],
            price=float(raw["price"]),
            fetched_at=datetime.now(timezone.utc),
        )

    @with_retry(retries=3, base_delay=0.5, max_delay=8.0)
    def get_klines(
        self,
        symbol: str,
        timeframe: str,
        *,
        limit: int = 300,
        end_time: int | None = None,
    ) -> list[Kline]:
        interval = _TIMEFRAME_MAP[timeframe]
        # Weight varies by limit; 5 is a safe default for limits up to ~500.
        self._limiter.acquire(5)
        try:
            raw = self._client.get_klines(
                symbol=symbol, interval=interval, limit=limit, endTime=end_time
            )
        except Exception as e:
            raise _map_binance_error(e) from e

        klines: list[Kline] = []
        for row in raw:
            klines.append(
                Kline(
                    symbol=symbol,
                    timeframe=timeframe,
                    open_time=datetime.fromtimestamp(row[0] / 1000, tz=timezone.utc),
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5]),
                )
            )
        return klines

    # --------------------------------------------------------------
    # Orders
    # --------------------------------------------------------------

    @with_retry(retries=3, base_delay=0.5, max_delay=8.0)
    def submit_order(self, request: OrderRequest) -> OrderResult:
        self._limiter.acquire(1)
        kwargs = {
            "symbol": request.symbol,
            "side": request.side,
            "type": request.order_type,
            "quantity": request.quantity,
        }
        if request.order_type == "LIMIT":
            kwargs["timeInForce"] = "GTC"
            kwargs["price"] = request.price
        if request.client_order_id:
            kwargs["newClientOrderId"] = request.client_order_id
        try:
            raw = self._client.create_order(**kwargs)
        except Exception as e:
            raise _map_binance_error(e) from e
        return self._parse_order(raw)

    @with_retry(retries=3, base_delay=0.5, max_delay=8.0)
    def get_order(self, symbol: str, exchange_order_id: str) -> OrderResult:
        self._limiter.acquire(1)
        try:
            raw = self._client.get_order(symbol=symbol, orderId=int(exchange_order_id))
        except Exception as e:
            raise _map_binance_error(e) from e
        return self._parse_order(raw)

    @with_retry(retries=3, base_delay=0.5, max_delay=8.0)
    def cancel_order(self, symbol: str, exchange_order_id: str) -> OrderResult:
        self._limiter.acquire(1)
        try:
            raw = self._client.cancel_order(symbol=symbol, orderId=int(exchange_order_id))
        except Exception as e:
            raise _map_binance_error(e) from e
        return self._parse_order(raw)

    # --------------------------------------------------------------
    # Account
    # --------------------------------------------------------------

    @with_retry(retries=3, base_delay=0.5, max_delay=8.0)
    def get_balance(self, asset: str) -> float:
        self._limiter.acquire(10)  # account endpoint is weight 10
        try:
            raw = self._client.get_asset_balance(asset=asset)
        except Exception as e:
            raise _map_binance_error(e) from e
        if not raw:
            return 0.0
        return float(raw.get("free", 0.0))

    # --------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------

    @staticmethod
    def _parse_order(raw: dict) -> OrderResult:
        filled = float(raw.get("executedQty", 0) or 0)
        quote = float(raw.get("cummulativeQuoteQty", 0) or 0)
        avg_price = quote / filled if filled > 0 and quote > 0 else None
        return OrderResult(
            exchange_order_id=str(raw["orderId"]),
            symbol=raw["symbol"],
            side=raw["side"],
            order_type=raw["type"],
            status=raw.get("status", "NEW"),
            requested_quantity=float(raw.get("origQty", 0) or 0),
            filled_quantity=filled,
            avg_fill_price=avg_price,
            client_order_id=raw.get("clientOrderId"),
        )
