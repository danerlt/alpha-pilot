"""Strategies — /api/strategies 受限策略集启停 (风控页, 联调#9)。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.common.response.response_schema import Response
from src.controllers.dependencies import get_current_user
from src.db.session import get_db
from src.schemas.strategy_read import StrategyCardRead, StrategyToggleOut
from src.services.strategy.strategy_registry import (
    list_strategies,
    set_strategy_enabled,
)
from src.services.system.permissions import require_permission

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


class StrategyToggleUpdate(BaseModel):
    enabled: bool


@router.get("", response_model=Response[list[StrategyCardRead]])
@api_response()
def get_strategies(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """受限策略集卡片: 启停状态 + 适用 regime (要求登录)。"""
    return list_strategies(db)


@router.patch("/{mode}", response_model=Response[StrategyToggleOut])
@api_response()
def toggle_strategy(
    mode: str,
    body: StrategyToggleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission("trade.engine_toggle")),
):
    """启停策略 (trader+): 被禁用模式的 OPEN_LONG 会被守卫 REJECT (真实生效)。"""
    return set_strategy_enabled(
        db, mode=mode, enabled=body.enabled, operator_user_id=current_user.id,
    )
