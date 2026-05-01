"""K线数据获取与持久化服务。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.core.exchange.binance_client import get_klines
from src.shared.config import get_settings
from src.models.candle import Candle

logger = logging.getLogger(__name__)

# V0.1 交易标的
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
TIMEFRAMES = ["15m", "1h"]

# python-binance 区间常量
_INTERVAL_MAP = {
    "15m": "15m",
    "1h": "1h",
}


def _ts_to_dt(ts_ms: int) -> datetime:
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)


def fetch_and_store_candles(
    db: Session,
    symbol: str,
    timeframe: str,
    limit: int = 200,
) -> int:
    """从 Binance 拉取 K 线并以 UPSERT 写入 DB，返回写入条数。"""
    settings = get_settings()
    interval = _INTERVAL_MAP.get(timeframe)
    if not interval:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    raw = get_klines(symbol=symbol, interval=interval, limit=limit)
    if not raw:
        logger.warning("No kline data returned for %s %s", symbol, timeframe)
        return 0

    rows = [
        {
            "trading_mode": settings.TRADING_MODE.value,
            "symbol": symbol,
            "timeframe": timeframe,
            "open_time": _ts_to_dt(int(k[0])),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        }
        for k in raw
    ]

    stmt = pg_insert(Candle.__table__).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["symbol", "timeframe", "open_time"],
        set_={
            "open": stmt.excluded.open,
            "high": stmt.excluded.high,
            "low": stmt.excluded.low,
            "close": stmt.excluded.close,
            "volume": stmt.excluded.volume,
        },
    )
    db.execute(stmt)
    db.commit()
    logger.info("Upserted %d candles for %s %s", len(rows), symbol, timeframe)
    return len(rows)


def get_candle_df(
    db: Session,
    symbol: str,
    timeframe: str,
    limit: int = 200,
) -> pd.DataFrame:
    """从 DB 查询最近 N 条 K 线，返回 DataFrame（按时间升序）。"""
    settings = get_settings()
    rows = (
        db.query(Candle)
        .filter(
            Candle.trading_mode == settings.TRADING_MODE.value,
            Candle.symbol == symbol,
            Candle.timeframe == timeframe,
        )
        .order_by(Candle.open_time.desc())
        .limit(limit)
        .all()
    )
    if not rows:
        return pd.DataFrame()

    data = [
        {
            "open_time": c.open_time,
            "open": float(c.open),
            "high": float(c.high),
            "low": float(c.low),
            "close": float(c.close),
            "volume": float(c.volume),
        }
        for c in rows
    ]
    df = pd.DataFrame(data).sort_values("open_time").reset_index(drop=True)
    return df
