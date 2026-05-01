"""Risk events — /api/risk-events (GET) / /api/risk-events/{id}/resolve (POST).

GET 要求登录, POST 要求 admin (危险操作: 解除熔断会让自动交易重新开仓)。

resolve 路径走 ManualOpsService.manual_resolve_circuit_breaker, 与
/api/commands/resolve-breaker 共享审计 + 事件路径 (post-Plan5 codereview Risk #3).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.common.exception.errors import DBException
from src.common.response.response_code import ErrorCode
from src.controllers.dependencies import get_adapter, get_current_user, require_admin
from src.services.manual_ops import ManualOpsService
from src.services.events.outbox import OutboxWriter
from src.shared.config import get_settings
from src.shared.db import get_db
from src.models.risk_event import RiskEvent

router = APIRouter(prefix="/api/risk-events", tags=["risk"])


class ResolveRiskEventRequest(BaseModel):
    """body 兼容性: reason 可选, 缺省给个标识来源的占位串. 前端最好显式传."""
    reason: str = "ui_resolve_via_risk_events"


@router.get("")
@api_response()
def list_risk_events(
    # post-Plan5 安全审计 M3: limit 加上限防 DoS / OOM
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    settings = get_settings()
    rows = (
        db.query(RiskEvent)
        .filter(RiskEvent.trading_mode == settings.TRADING_MODE.value)
        .order_by(RiskEvent.triggered_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id, "event_type": r.event_type, "symbol": r.symbol,
            "description": r.description, "resolved": r.resolved,
            "triggered_at": r.triggered_at.isoformat(),
            "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
        }
        for r in rows
    ]


@router.post("/{event_id}/resolve")
@api_response()
def resolve_risk_event(
    event_id: int,
    body: ResolveRiskEventRequest | None = None,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    """手动解除熔断事件 (admin only).

    走 ManualOpsService 统一路径 — 写 audit_logs + 发 manual.override 事件,
    避免与 /api/commands/resolve-breaker/{id} 形成审计盲区 (Risk #3).
    """
    settings = get_settings()
    # trading_mode 守卫: 不允许跨模式 resolve
    event = (
        db.query(RiskEvent)
        .filter(
            RiskEvent.trading_mode == settings.TRADING_MODE.value,
            RiskEvent.id == event_id,
        )
        .first()
    )
    if not event:
        raise DBException(error_code=ErrorCode.NOT_FOUND, message="Risk event not found")

    reason = body.reason if body is not None else "ui_resolve_via_risk_events"
    svc = ManualOpsService(db, get_adapter(), outbox=OutboxWriter())
    ok = svc.manual_resolve_circuit_breaker(
        risk_event_id=event_id,
        reason=reason,
        operator_user_id=current_admin.id,
    )
    db.commit()
    if not ok:
        # ManualOpsService 内部找不到 (理论上前面 query 已找到, 防御性兜底)
        raise DBException(error_code=ErrorCode.NOT_FOUND, message="Risk event not found")
    return {"message": "Risk event resolved", "id": event_id}
