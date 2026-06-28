"""Attribution — /api/attribution (GET 逐笔) /summary (GET 聚合) /generate (POST)。

GET 要求登录, POST 要求 admin。PRD 8.1.3 交易归因分析 (只读历史交易, 零决策影响)。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.configs.app_configs import get_settings
from src.controllers.dependencies import get_current_user, require_admin
from src.cruds.trade_attribution_crud import trade_attribution_crud
from src.db.session import get_db
from src.services.insight.attribution.service import AttributionService

router = APIRouter(prefix="/api/attribution", tags=["attribution"])


@router.get("")
@api_response()
def list_attributions(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rows = trade_attribution_crud.list_recent(db, limit=limit)
    return [
        {
            "id": r.id,
            "trade_id": r.trade_id,
            "by_symbol": r.by_symbol,
            "by_time_bucket": r.by_time_bucket,
            "by_exit_reason": r.by_exit_reason,
            "narrative": r.narrative,
            "generated_at": r.generated_at.isoformat() if r.generated_at else None,
        }
        for r in rows
    ]


@router.get("/summary")
@api_response()
def attribution_summary(
    window_days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    settings = get_settings()
    s = AttributionService(db).summary_only(
        trading_mode=settings.TRADING_MODE.value, window_days=window_days,
    )
    return {
        "total_trades": s.total_trades,
        "total_pnl": s.total_pnl,
        "by_symbol": s.by_symbol,
        "by_exit_reason": s.by_exit_reason,
        "by_regime": s.by_regime,
        "by_time_bucket": s.by_time_bucket,
    }


@router.post("/generate")
@api_response()
def generate_attribution(
    window_days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    """手动触发逐笔归因 (admin only)。"""
    settings = get_settings()
    s = AttributionService(db).attribute_window(
        trading_mode=settings.TRADING_MODE.value, window_days=window_days,
    )
    db.commit()
    return {"message": "Attribution generated", "trades": s.total_trades}
