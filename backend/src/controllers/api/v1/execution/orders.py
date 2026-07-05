"""Orders — /api/orders 手动下单域 (handoff P2 §3.2)。

权限口径: 手动下单是高危写操作, 当前角色体系仅 user/admin 两级, 暂定
require_admin; P4 RBAC (owner/admin/trader/viewer) 落地后放宽为 trader+。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.configs.app_configs import get_settings
from src.controllers.dependencies import get_adapter, require_admin
from src.db.session import get_db
from src.schemas.manual_order import ManualOrderCreate
from src.services.execution.manual_trade import ManualTradeService

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _trading_mode() -> str:
    settings = get_settings()
    mode = settings.TRADING_MODE
    return mode.value if hasattr(mode, "value") else mode


@router.post("/precheck")
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
