"""Performance — /api/performance (handoff 3.8, strategy 域扩展)。全部登录可见。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.common.response.response_schema import Response
from src.configs.app_configs import get_settings
from src.controllers.dependencies import get_current_user
from src.db.session import get_db
from src.schemas.performance_read import (
    AttributionBucketRead,
    MonthlyPnlRead,
    PerformanceSummaryOut,
)
from src.services.reporting.performance import PerformanceService

router = APIRouter(prefix="/api/performance", tags=["performance"])


def _mode() -> str:
    mode = get_settings().TRADING_MODE
    return mode.value if hasattr(mode, "value") else mode


@router.get("/summary", response_model=Response[PerformanceSummaryOut])
@api_response()
def performance_summary(
    range_days: int = Query(default=90, ge=7, le=365, alias="range"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """6 指标 + vs HODL 基准曲线 + 主控台聚合磁贴 (联调缺口#5)。"""
    return PerformanceService(db).summary(trading_mode=_mode(), range_days=range_days)


@router.get("/monthly", response_model=Response[list[MonthlyPnlRead]])
@api_response()
def performance_monthly(
    months: int = Query(default=12, ge=1, le=36),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """月度 PnL (零轴柱图数据源)。"""
    return PerformanceService(db).monthly(trading_mode=_mode(), months=months)


@router.get("/attribution", response_model=Response[list[AttributionBucketRead]])
@api_response()
def performance_attribution(
    dim: str = Query(default="symbol", max_length=20),
    range_days: int = Query(default=90, ge=7, le=365, alias="range"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """归因分解: dim=symbol|strategy|trigger。"""
    return PerformanceService(db).attribution(
        trading_mode=_mode(), dim=dim, range_days=range_days,
    )
