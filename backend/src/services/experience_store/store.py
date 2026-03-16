"""经验库服务 — 写入和检索已平仓交易的结构化经验记录（V0.1 无 embedding，纯结构化查询）。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from src.shared.config import get_settings
from src.shared.models.experience import ExperienceRecord
from src.shared.models.trade import Trade

logger = logging.getLogger(__name__)


def record_trade_experience(
    db: Session,
    trade: Trade,
    indicator_snapshot: dict[str, Any] | None = None,
) -> ExperienceRecord:
    """将已完成 trade 写入经验库。"""
    settings = get_settings()
    record = ExperienceRecord(
        trading_mode=settings.TRADING_MODE.value,
        trade_id=trade.id,
        symbol=trade.symbol,
        timeframe="1h",
        regime=trade.regime or "unknown",
        strategy_mode=trade.strategy_mode or "observation",
        indicator_snapshot=indicator_snapshot,
        action="CLOSE_LONG",
        entry_price=float(trade.entry_price),
        exit_price=float(trade.exit_price),
        pnl=float(trade.pnl),
        pnl_pct=float(trade.pnl_pct),
        exit_reason=trade.exit_reason,
        holding_seconds=trade.holding_seconds,
        recorded_at=datetime.now(tz=timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(
        "Experience recorded for trade_id=%d symbol=%s pnl=%.4f",
        trade.id, trade.symbol, float(trade.pnl),
    )
    return record


def get_recent_experience(
    db: Session,
    symbol: str,
    limit: int = 5,
) -> list[dict]:
    """检索最近 N 条同币种经验，返回字典列表（用于 prompt 构建）。"""
    settings = get_settings()
    records = (
        db.query(ExperienceRecord)
        .filter(
            ExperienceRecord.trading_mode == settings.TRADING_MODE.value,
            ExperienceRecord.symbol == symbol,
        )
        .order_by(ExperienceRecord.recorded_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "symbol": r.symbol,
            "pnl_pct": float(r.pnl_pct),
            "exit_reason": r.exit_reason,
            "strategy_mode": r.strategy_mode,
            "regime": r.regime,
            "holding_seconds": r.holding_seconds,
        }
        for r in records
    ]
