"""Trades — /api/trades."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.controllers.dependencies import get_current_user
from src.shared.config import get_settings
from src.shared.db import get_db
from src.models.trade import Trade

router = APIRouter(prefix="/api/trades", tags=["trades"])


@router.get("")
def list_trades(
    # post-Plan5 安全审计 M3: limit 加上限防 DoS / OOM
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """返回最近 N 条已完成交易记录 (要求登录)。"""
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
