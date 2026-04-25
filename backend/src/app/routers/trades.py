"""Trades — /api/trades."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.shared.config import get_settings
from src.shared.db import get_db

router = APIRouter(prefix="/api/trades", tags=["trades"])


@router.get("")
def list_trades(limit: int = 50, db: Session = Depends(get_db)):
    """返回最近 N 条已完成交易记录。"""
    from src.shared.models.trade import Trade
    settings = get_settings()
    rows = (
        db.query(Trade)
        .filter(Trade.trading_mode == settings.TRADING_MODE.value)
        .order_by(Trade.closed_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": t.id, "symbol": t.symbol,
            "quantity": float(t.quantity),
            "entry_price": float(t.entry_price),
            "exit_price": float(t.exit_price),
            "pnl": float(t.pnl), "pnl_pct": float(t.pnl_pct),
            "exit_reason": t.exit_reason,
            "strategy_mode": t.strategy_mode,
            "regime": t.regime,
            "opened_at": t.opened_at.isoformat(),
            "closed_at": t.closed_at.isoformat(),
            "holding_seconds": t.holding_seconds,
        }
        for t in rows
    ]
