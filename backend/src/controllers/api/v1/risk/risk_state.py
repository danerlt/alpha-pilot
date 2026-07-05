"""Risk state — GET /api/risk/state (webapp 架构 B2)。

前端顶栏风控胶囊/HALTED 联动的主动拉取口; 状态迁移的实时推送走
`risk.state` 事件 (pause/resume/熔断触发与解除时发布)。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.common.response.response_schema import Response
from src.configs.app_configs import get_settings
from src.controllers.dependencies import get_current_user
from src.db.session import get_db
from src.schemas.risk_read import RiskLimitsOut, RiskStateOut
from src.services.risk.risk_state import RiskStateService

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("/state", response_model=Response[RiskStateOut])
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


@router.get("/limits", response_model=Response[RiskLimitsOut])
@api_response()
def get_risk_limits(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """硬风控阈值只读视图 (联调缺口#7): active RiskProfile + runtime 覆盖生效值。"""
    from src.cruds.account_entity_crud import risk_profile_crud

    settings = get_settings()
    profile = risk_profile_crud.find_active(db)
    return {
        "max_position_size_pct": float(settings.MAX_POSITION_SIZE_PCT),
        "max_daily_loss_pct": float(settings.MAX_DAILY_LOSS_PCT),
        "max_consecutive_losses": int(settings.MAX_CONSECUTIVE_LOSSES),
        "max_single_risk_pct": float(settings.MAX_SINGLE_RISK_PCT),
        "min_rr_ratio": float(profile.min_rr_ratio) if profile else None,
        "sl_atr_min_mult": float(profile.sl_atr_min_mult) if profile else None,
        "sl_atr_max_mult": float(profile.sl_atr_max_mult) if profile else None,
    }
