"""Risk state — GET /api/risk/state (webapp 架构 B2)。

前端顶栏风控胶囊/HALTED 联动的主动拉取口; 状态迁移的实时推送走
`risk.state` 事件 (pause/resume/熔断触发与解除时发布)。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.configs.app_configs import get_settings
from src.controllers.dependencies import get_current_user
from src.db.session import get_db
from src.services.risk.risk_state import RiskStateService

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("/state")
@api_response()
def get_risk_state(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """风控状态快照: OK|WARN|HALTED + 日亏/仓位占比/regime (要求登录)。"""
    settings = get_settings()
    mode = settings.TRADING_MODE
    return RiskStateService(db).compute(
        trading_mode=mode.value if hasattr(mode, "value") else mode,
    )
