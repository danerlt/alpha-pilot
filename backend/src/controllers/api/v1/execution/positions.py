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
from src.common.enums import PositionStatus
from src.common.response.response_schema import Response
from src.configs.app_configs import get_settings
from src.controllers.dependencies import get_adapter, get_current_user
from src.db.session import get_db
from src.models.position import Position
from src.schemas.execution_read import PositionRead, SltpOut
from src.schemas.manual_order import SltpUpdate
from src.services.events.outbox import OutboxWriter
from src.services.execution.manual_trade import ManualTradeService
from src.services.system.permissions import require_permission

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.get("", response_model=Response[list[PositionRead]])
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
    # 联调缺口#4: strategy_mode 决策反查 + 仓位占比(市值/总权益)
    from src.cruds.account_crud import account_snapshot_crud
    from src.models.decision import AIDecision

    decision_ids = [p.ai_decision_id for p in rows if p.ai_decision_id]
    modes: dict[int, str | None] = {}
    if decision_ids:
        for d in db.query(AIDecision).filter(AIDecision.id.in_(decision_ids)).all():
            modes[d.id] = d.strategy_mode
    snap = account_snapshot_crud.find_latest(
        db, trading_mode=settings.TRADING_MODE.value,
    )
    total = float(snap.total_balance_usdt) if snap else 0.0
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
            "strategy_mode": modes.get(p.ai_decision_id) if p.ai_decision_id else None,
            "position_pct": (
                float(p.quantity) * float(p.current_price or p.entry_price) / total
                if total > 0 else None
            ),
        }
        for p in rows
    ]


@router.patch("/{position_id}/sltp", response_model=Response[SltpOut])
@api_response()
def update_position_sltp(
    position_id: int,
    body: SltpUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_permission("trade.manual_order")),
    adapter=Depends(get_adapter),
):
    """修改持仓 SL/TP (handoff P2 §3.2): 走守卫规则校验 + 审计。

    权限 (P4 RBAC): trade.manual_order → owner/admin/trader。
    """
    settings = get_settings()
    mode = settings.TRADING_MODE
    return ManualTradeService(db, adapter, outbox=OutboxWriter()).update_sltp(
        position_id=position_id, body=body,
        trading_mode=mode.value if hasattr(mode, "value") else mode,
        operator_user_id=current_admin.id,
    )
