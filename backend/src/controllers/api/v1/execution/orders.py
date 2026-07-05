"""Orders — /api/orders 手动下单域 (handoff P2 §3.2)。

权限口径: 手动下单是高危写操作, 当前角色体系仅 user/admin 两级, 暂定
require_admin; P4 RBAC (owner/admin/trader/viewer) 落地后放宽为 trader+。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.common.response.response_schema import Response
from src.configs.app_configs import get_settings
from src.controllers.dependencies import get_adapter, get_current_user, require_admin
from src.db.session import get_db
from src.schemas.execution_read import OrderListItemRead, OrderPlacedOut, PrecheckOut
from src.schemas.manual_order import ManualOrderCreate
from src.services.events.outbox import OutboxWriter
from src.services.execution.manual_trade import ManualTradeService

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _trading_mode() -> str:
    settings = get_settings()
    mode = settings.TRADING_MODE
    return mode.value if hasattr(mode, "value") else mode


@router.post("/precheck", response_model=Response[PrecheckOut])
@api_response()
def precheck_order(
    body: ManualOrderCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
    adapter=Depends(get_adapter),
):
    """守卫预检: 逐项 PASS/FAIL + 总判定 (只读, 下单时服务端会再跑一遍)。"""
    return ManualTradeService(db, adapter).precheck(
        body=body, trading_mode=_trading_mode(),
    ).to_dict()


@router.post("", response_model=Response[OrderPlacedOut])
@api_response()
def place_order(
    body: ManualOrderCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
    adapter=Depends(get_adapter),
):
    """手动下单: 服务端重跑守卫, HALTED 仅接受 reduce-only 平仓, 幂等 + 审计。"""
    return ManualTradeService(db, adapter, outbox=OutboxWriter()).place_order(
        body=body, trading_mode=_trading_mode(),
        operator_user_id=current_admin.id,
    )


@router.get("", response_model=Response[list[OrderListItemRead]])
@api_response()
def list_orders(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """订单列表 (联调缺口#3): 近 N 条, 新的在前 (要求登录)。"""
    from src.cruds.order_crud import order_crud

    rows = order_crud.find_latest(db, trading_mode=_trading_mode(), limit=limit)
    return [
        {
            "id": o.id, "symbol": o.symbol, "side": o.side,
            "order_type": o.order_type, "status": o.status,
            "quantity": float(o.quantity),
            "price": float(o.price) if o.price is not None else None,
            "avg_fill_price": float(o.avg_fill_price) if o.avg_fill_price is not None else None,
            "trace_id": o.trace_id,
            "position_id": o.position_id,
            "ai_decision_id": o.ai_decision_id,
            "submitted_at": o.submitted_at.isoformat(),
            "filled_at": o.filled_at.isoformat() if o.filled_at else None,
        }
        for o in rows
    ]
