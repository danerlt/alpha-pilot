"""Abstract ExchangeAdapter. Concrete implementations must not leak exchange-specific types."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from src.core.exchange.types import (
    FuturesMetrics,
    Kline,
    OrderRequest,
    OrderResult,
    Ticker,
    Ticker24h,
)


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

    # ------------------------------------------------------------------
    # 行情装饰数据 (handoff P2) — 非抽象默认实现, 既有 stub 无需变更;
    # 不可用时返回 None, 调用方按 None 降级展示。
    # ------------------------------------------------------------------

    def get_ticker_24h(self, symbol: str) -> Ticker24h | None:
        return None

    def get_futures_metrics(self, symbol: str) -> FuturesMetrics | None:
        return None

    def get_account_permissions(self, *, raise_on_error: bool = False) -> dict | None:
        """API Key 权限探测 (handoff 3.6): {read, trade, withdraw}; 不可用返 None。

        raise_on_error=True 时上抛真实异常 (供设置页测试连接透出具体原因)。
        """
        return None
