"""Positions endpoints — /api/positions /api/positions/{id}/close /api/positions/close-all."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.shared.config import get_settings
from src.shared.db import get_db
from src.shared.enums import PositionStatus

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.get("")
def list_positions(db: Session = Depends(get_db)):
    """列出所有开仓持仓。"""
    from src.shared.models.position import Position
    settings = get_settings()
    rows = (
        db.query(Position)
        .filter(
            Position.trading_mode == settings.TRADING_MODE.value,
            Position.status == PositionStatus.OPEN.value,
        )
        .order_by(Position.opened_at.desc())
        .all()
    )
    return [
        {
            "id": p.id, "symbol": p.symbol,
            "quantity": float(p.quantity),
            "entry_price": float(p.entry_price),
            "current_price": float(p.current_price or 0),
            "stop_loss": float(p.stop_loss),
            "take_profit": float(p.take_profit) if p.take_profit else None,
            "unrealized_pnl": float(p.unrealized_pnl or 0),
            "unrealized_pnl_pct": float(p.unrealized_pnl_pct or 0),
            "opened_at": p.opened_at.isoformat(),
        }
        for p in rows
    ]


@router.post("/{position_id}/close")
def manual_close_position(position_id: int, db: Session = Depends(get_db)):
    """手动平仓 (绕过 AI 风控, 直接执行)。"""
    from src.services.order_execution.executor import close_long
    from src.shared.enums import TradeExitReason
    from src.shared.models.position import Position
    settings = get_settings()
    pos = (
        db.query(Position)
        .filter(
            Position.trading_mode == settings.TRADING_MODE.value,
            Position.id == position_id,
            Position.status == PositionStatus.OPEN.value,
        )
        .first()
    )
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found or already closed")
    order = close_long(db, pos, TradeExitReason.MANUAL_CLOSE)
    if order is None:
        raise HTTPException(status_code=500, detail="Failed to close position")
    return {"message": "Position closed", "order_id": order.id}


@router.post("/close-all")
def close_all_positions(db: Session = Depends(get_db)):
    """一键全部平仓 (绕过所有风控)。"""
    from src.services.order_execution.executor import close_long
    from src.shared.enums import TradeExitReason
    from src.shared.models.position import Position
    settings = get_settings()
    open_positions = (
        db.query(Position)
        .filter(
            Position.trading_mode == settings.TRADING_MODE.value,
            Position.status == PositionStatus.OPEN.value,
        )
        .all()
    )
    closed = []
    for pos in open_positions:
        order = close_long(db, pos, TradeExitReason.MANUAL_CLOSE)
        if order:
            closed.append(pos.id)
    return {"closed_positions": closed, "count": len(closed)}
