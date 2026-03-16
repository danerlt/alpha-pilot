"""Binance API 客户端 — 统一封装 testnet/mainnet 切换。"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from binance.client import Client
from src.shared.config import get_settings
from src.shared.enums import TradingMode

logger = logging.getLogger(__name__)

TESTNET_API_URL = "https://testnet.binance.vision/api"


@lru_cache(maxsize=1)
def get_binance_client() -> Client:
    settings = get_settings()
    client = Client(
        api_key=settings.BINANCE_API_KEY,
        api_secret=settings.BINANCE_API_SECRET,
        testnet=(settings.TRADING_MODE == TradingMode.TESTNET),
    )
    if settings.TRADING_MODE == TradingMode.TESTNET:
        client.API_URL = TESTNET_API_URL
    logger.info("Binance client initialised (mode=%s)", settings.TRADING_MODE.value)
    return client


def get_klines(symbol: str, interval: str, limit: int = 500) -> list[list[Any]]:
    """Return raw kline data from Binance.

    Each element: [open_time, open, high, low, close, volume, close_time, ...]
    """
    client = get_binance_client()
    return client.get_klines(symbol=symbol, interval=interval, limit=limit)


def get_symbol_ticker(symbol: str) -> dict[str, Any]:
    """Return latest price ticker."""
    return get_binance_client().get_symbol_ticker(symbol=symbol)


def get_account_info() -> dict[str, Any]:
    """Return full account information (balances, etc.)."""
    return get_binance_client().get_account()


def get_open_orders(symbol: str | None = None) -> list[dict[str, Any]]:
    kwargs: dict[str, Any] = {}
    if symbol:
        kwargs["symbol"] = symbol
    return get_binance_client().get_open_orders(**kwargs)


def get_all_orders(symbol: str, limit: int = 50) -> list[dict[str, Any]]:
    return get_binance_client().get_all_orders(symbol=symbol, limit=limit)


def create_order(
    symbol: str,
    side: str,
    order_type: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Place an order. side: BUY/SELL, order_type: MARKET/LIMIT."""
    client = get_binance_client()
    return client.create_order(symbol=symbol, side=side, type=order_type, **kwargs)


def cancel_order(symbol: str, order_id: int) -> dict[str, Any]:
    return get_binance_client().cancel_order(symbol=symbol, orderId=order_id)


def get_order(symbol: str, order_id: int) -> dict[str, Any]:
    return get_binance_client().get_order(symbol=symbol, orderId=order_id)
