"""Account — /api/account."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.common.response.response_schema import Response
from src.configs.app_configs import get_settings
from src.controllers.dependencies import get_current_user
from src.db.session import get_db
from src.models.account import AccountSnapshot
from src.schemas.execution_read import AccountSnapshotRead, EquityPointRead

router = APIRouter(prefix="/api/account", tags=["account"])


@router.get("", response_model=Response[AccountSnapshotRead])
@api_response()
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


@router.get("/history", response_model=Response[list[EquityPointRead]])
@api_response()
def account_history(
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """权益曲线序列 (联调缺口#2): 近 N 个快照点, 时间正序。"""
    from src.cruds.account_crud import account_snapshot_crud

    settings = get_settings()
    rows = account_snapshot_crud.find_series(
        db, trading_mode=settings.TRADING_MODE.value, limit=limit,
    )
    return [
        {"ts": r.snapshot_at.isoformat(), "equity": float(r.total_balance_usdt)}
        for r in rows
    ]
