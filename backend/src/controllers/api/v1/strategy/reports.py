"""Reports — /api/reports (GET) /api/reports/generate (POST).

GET 要求登录, POST 要求 admin (生成行为修改 DB)。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.configs.app_configs import get_settings
from src.controllers.dependencies import get_current_user, require_admin
from src.db.session import get_db
from src.models.report import DailyReport
from src.services.reporting.reporter import generate_daily_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
@api_response()
def list_reports(
    # post-Plan5 安全审计 M3: limit 加上限防 DoS / OOM
    limit: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    settings = get_settings()
    rows = (
        db.query(DailyReport)
        .filter(DailyReport.trading_mode == settings.TRADING_MODE.value)
        .order_by(DailyReport.report_date.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "report_date": r.report_date.isoformat(),
            "total_trades": r.total_trades,
            "winning_trades": r.winning_trades,
            "losing_trades": r.losing_trades,
            "win_rate": float(r.win_rate) if r.win_rate else None,
            "total_pnl": float(r.total_pnl),
            "total_pnl_pct": float(r.total_pnl_pct),
            "max_drawdown": float(r.max_drawdown) if r.max_drawdown else None,
            "risk_events_count": r.risk_events_count,
        }
        for r in rows
    ]


@router.post("/generate")
@api_response()
def generate_report(
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    """手动触发今日日报生成 (admin only)。"""
    report = generate_daily_report(db)
    return {"message": "Report generated", "report_date": report.report_date.isoformat()}
