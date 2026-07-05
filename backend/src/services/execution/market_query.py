"""MarketQueryService — 行情查询聚合 (handoff P2 §3.1)。

只读服务, 服务行情页三个 REST 端点:
  - get_klines: DB 新鲜够量 → 走 candles 表; 否则交易所直取透传
    (不落库, 避免与 MarketDataService 的 delete-and-insert 幂等窗口冲突);
    交易所失败降级返 DB 既有数据。
  - get_ticker: 24h 统计 + USDT-M 公共指标 (装饰性, 不可用为 None)。
  - list_symbols: symbol_config 启用清单 + 行情/持仓/regime 聚合。
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from src.common.exception.errors import ParamsException
from src.core.exchange.adapter import ExchangeAdapter
from src.cruds.candle_crud import candle_crud
from src.cruds.position_crud import position_crud
from src.cruds.regime_crud import regime_snapshot_crud
from src.cruds.symbol_config_crud import symbol_config_crud

logger = logging.getLogger(__name__)

_INTERVAL_SECONDS = {
    "1m": 60, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400,
}


class MarketQueryService:
    def __init__(self, session: Session, adapter: ExchangeAdapter):
        self._session = session
        self._adapter = adapter

    def get_klines(
        self,
        *,
        trading_mode: str,
        symbol: str,
        interval: str,
        limit: int,
        account_id: int = 1,
    ) -> list[dict]:
        if interval not in _INTERVAL_SECONDS:
            raise ParamsException(
                f"interval 必须是 {sorted(_INTERVAL_SECONDS)} 之一, got {interval!r}"
            )

        rows = candle_crud.find_latest(
            self._session,
            account_id=account_id, trading_mode=trading_mode,
            symbol=symbol, timeframe=interval, limit=limit,
        )
        if self._db_is_sufficient(rows, interval=interval, limit=limit):
            return [self._candle_to_dict(c) for c in rows]

        try:
            klines = self._adapter.get_klines(symbol, interval, limit=limit)
            return [
                {
                    "open_time": k.open_time.isoformat(),
                    "open": k.open, "high": k.high, "low": k.low,
                    "close": k.close, "volume": k.volume,
                }
                for k in klines
            ]
        except Exception:
            logger.warning(
                "get_klines exchange fetch failed for %s %s; fallback to DB (%d rows)",
                symbol, interval, len(rows), exc_info=True,
            )
            return [self._candle_to_dict(c) for c in rows]

    @staticmethod
    def _db_is_sufficient(rows, *, interval: str, limit: int) -> bool:
        """行数够 且 最新一根距今 < 2×interval 视为可直接服务。"""
        if len(rows) < limit:
            return False
        from datetime import datetime, timezone

        latest = rows[-1].open_time
        if latest.tzinfo is None:
            latest = latest.replace(tzinfo=timezone.utc)
        age = (datetime.now(tz=timezone.utc) - latest).total_seconds()
        return age < 2 * _INTERVAL_SECONDS[interval]

    @staticmethod
    def _candle_to_dict(c) -> dict:
        return {
            "open_time": c.open_time.isoformat(),
            "open": float(c.open), "high": float(c.high), "low": float(c.low),
            "close": float(c.close), "volume": float(c.volume),
        }

    def get_ticker(self, *, symbol: str) -> dict:
        """24h 统计 + USDT-M 公共指标; 24h 不可用时以现价兜底, 其余字段 None。"""
        t24 = self._adapter.get_ticker_24h(symbol)
        fm = self._adapter.get_futures_metrics(symbol)
        if t24 is not None:
            base = {
                "symbol": t24.symbol,
                "last_price": t24.last_price,
                "price_change_pct": t24.price_change_pct,
                "high_24h": t24.high_24h,
                "low_24h": t24.low_24h,
                "volume_24h": t24.volume_24h,
                "quote_volume_24h": t24.quote_volume_24h,
            }
        else:
            ticker = self._adapter.get_ticker(symbol)
            base = {
                "symbol": symbol,
                "last_price": ticker.price,
                "price_change_pct": None,
                "high_24h": None, "low_24h": None,
                "volume_24h": None, "quote_volume_24h": None,
            }
        base.update({
            "mark_price": fm.mark_price if fm else None,
            "index_price": fm.index_price if fm else None,
            "funding_rate": fm.funding_rate if fm else None,
            "next_funding_time": (
                fm.next_funding_time.isoformat()
                if fm and fm.next_funding_time else None
            ),
            "open_interest": fm.open_interest if fm else None,
        })
        return base

    def list_symbols(self, *, trading_mode: str, account_id: int = 1) -> list[dict]:
        """自选列表: 启用交易对 × 24h行情 / 持仓中 / 最新 regime。

        单 symbol 行情失败只置空该行字段, 不整体失败。
        """
        configs = symbol_config_crud.find_enabled(self._session)
        open_symbols = position_crud.find_open_symbols(
            self._session, trading_mode=trading_mode, account_id=account_id,
        )
        out: list[dict] = []
        for cfg in configs:
            t24 = self._adapter.get_ticker_24h(cfg.symbol)
            regime_row = regime_snapshot_crud.find_latest_by_symbol(
                self._session, trading_mode=trading_mode,
                symbol=cfg.symbol, account_id=account_id,
            )
            out.append({
                "symbol": cfg.symbol,
                "base_asset": cfg.base_asset,
                "last_price": t24.last_price if t24 else None,
                "price_change_pct": t24.price_change_pct if t24 else None,
                "quote_volume_24h": t24.quote_volume_24h if t24 else None,
                "has_position": cfg.symbol in open_symbols,
                "regime": regime_row.regime if regime_row else None,
            })
        return out
