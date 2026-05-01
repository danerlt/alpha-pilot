"""Positions endpoints — /api/positions (GET only).

旧的 POST /api/positions/{id}/close 和 /api/positions/close-all 已迁移到
/api/commands/close-position/{id} 和 /api/commands/close-all (Critical fix C3)。
新版走 ManualOpsService 写 audit_logs + 发 manual.override 事件 + 要求
confirmation='CLOSE ALL', 旧版的弱保护版本不再可用。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.controllers.dependencies import get_current_user
from src.shared.config import get_settings
from src.shared.db import get_db
from src.shared.enums import PositionStatus
from src.models.position import Position

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.get("")
@api_response()
def list_positions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """列出所有开仓持仓 (要求登录)。"""
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
