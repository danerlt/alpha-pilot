"""Account — /api/account."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.controllers.dependencies import get_current_user
from src.shared.config import get_settings
from src.shared.db import get_db
from src.models.account import AccountSnapshot

router = APIRouter(prefix="/api/account", tags=["account"])


@router.get("")
def get_account(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """返回最新账户快照 (要求登录)。"""
    settings = get_settings()
    snap = (
        db.query(AccountSnapshot)
        .filter(AccountSnapshot.trading_mode == settings.TRADING_MODE.value)
        .order_by(AccountSnapshot.snapshot_at.desc())
        .first()
    )
    if not snap:
        return {"message": "No account snapshot available"}
    return {
        "total_balance_usdt": float(snap.total_balance_usdt),
        "available_balance_usdt": float(snap.available_balance_usdt),
        "unrealized_pnl": float(snap.unrealized_pnl),
        "daily_pnl": float(snap.daily_pnl),
        "daily_pnl_pct": float(snap.daily_pnl_pct),
        "snapshot_at": snap.snapshot_at.isoformat(),
    }
