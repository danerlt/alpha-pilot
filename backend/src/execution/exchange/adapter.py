"""Abstract ExchangeAdapter. Concrete implementations must not leak exchange-specific types."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from src.execution.exchange.types import Kline, OrderRequest, OrderResult, Ticker


class ExchangeAdapter(ABC):
    """Single abstraction over a spot exchange.

    trading_mode is fixed at construction time so the business layer never
    branches on testnet vs mainnet — an instance targets exactly one mode.
    """

    @abstractmethod
    def get_ticker(self, symbol: str) -> Ticker: ...

    @abstractmethod
    def get_klines(
        self,
        symbol: str,
        timeframe: str,
        *,
        limit: int = 300,
        end_time: int | None = None,
    ) -> list[Kline]: ...

    @abstractmethod
    def submit_order(self, request: OrderRequest) -> OrderResult: ...

    @abstractmethod
    def get_order(self, symbol: str, exchange_order_id: str) -> OrderResult: ...

    @abstractmethod
    def cancel_order(self, symbol: str, exchange_order_id: str) -> OrderResult: ...

    @abstractmethod
    def get_balance(self, asset: str) -> float: ...

    @property
    @abstractmethod
    def trading_mode(self) -> Literal["testnet", "mainnet"]: ...
