"""MarketDataService — 从 ExchangeAdapter 拉 K 线, UPSERT candles, 发 candle.closed 事件。

用 Plan 1 的 BinanceAdapter(或 mock) 作为数据源。写库走 delete-and-insert
的幂等模式（同 symbol × timeframe × open_time 不重复），这样 sqlite 单测
和 postgres 生产都能 work 而不用 dialect-specific UPSERT。

若提供 outbox, 每根新 K 线都产生一条 CandleClosed outbox 行, 由 Plan 1
的 EventShuttle 搬到 Redis Streams。
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import delete
from sqlalchemy.orm import Session

from src.services.events.contracts import CandleClosed
from src.services.events.outbox import OutboxWriter
from src.core.exchange.adapter import ExchangeAdapter
from src.models.candle import Candle

logger = logging.getLogger(__name__)


class MarketDataService:
    def __init__(
        self,
        session: Session,
        adapter: ExchangeAdapter,
        outbox: Optional[OutboxWriter] = None,
    ):
        self._session = session
        self._adapter = adapter
        self._outbox = outbox

    def fetch_and_store(
        self,
        *,
        account_id: int,
        trading_mode: str,
        symbol: str,
        timeframe: str,
        trace_id: str,
        limit: int = 300,
    ) -> int:
        """拉 limit 根 K 线 → delete-and-insert → 发 CandleClosed 事件。返回写入行数。"""
        klines = self._adapter.get_klines(symbol, timeframe, limit=limit)
        if not klines:
            logger.warning("no klines returned for %s %s", symbol, timeframe)
            return 0

        open_times = [k.open_time for k in klines]
        # 幂等: 先删已存在的同 key 行, 再 bulk insert
        self._session.execute(
            delete(Candle).where(
                Candle.account_id == account_id,
                Candle.trading_mode == trading_mode,
                Candle.symbol == symbol,
                Candle.timeframe == timeframe,
                Candle.open_time.in_(open_times),
            )
        )

        for k in klines:
            self._session.add(Candle(
                account_id=account_id,
                trading_mode=trading_mode,
                symbol=symbol,
                timeframe=timeframe,
                open_time=k.open_time,
                open=k.open,
                high=k.high,
                low=k.low,
                close=k.close,
                volume=k.volume,
            ))

        self._session.flush()

        if self._outbox is not None:
            for k in klines:
                self._outbox.record(
                    self._session,
                    aggregate_type="candle",
                    aggregate_id=None,
                    event=CandleClosed(
                        symbol=symbol, timeframe=timeframe,
                        open_time=k.open_time,
                        open=k.open, high=k.high, low=k.low,
                        close=k.close, volume=k.volume,
                    ),
                    account_id=account_id,
                    trading_mode=trading_mode,
                    trace_id=trace_id,
                )

        return len(klines)
