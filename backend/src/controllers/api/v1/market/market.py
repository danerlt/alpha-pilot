"""Market — /api/market (handoff P2 §3.1 行情域)。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.configs.app_configs import get_settings
from src.controllers.dependencies import get_adapter, get_current_user
from src.db.session import get_db
from src.services.execution.market_query import MarketQueryService

router = APIRouter(prefix="/api/market", tags=["market"])


def _trading_mode() -> str:
    settings = get_settings()
    mode = settings.TRADING_MODE
    return mode.value if hasattr(mode, "value") else mode


@router.get("/klines")
@api_response()
def get_klines(
    symbol: str = Query(min_length=1, max_length=20),
    interval: str = Query(default="1h", max_length=10),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    adapter=Depends(get_adapter),
):
    """K线查询 (要求登录): DB 新鲜够量走库, 否则交易所直取。"""
    return MarketQueryService(db, adapter).get_klines(
        trading_mode=_trading_mode(), symbol=symbol, interval=interval, limit=limit,
    )
