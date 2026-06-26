"""Strategy scores — /api/strategy-scores (GET) /generate (POST)。

GET 要求登录, POST 要求 admin (触发评分写 DB)。PRD 8.2.5 策略评分器。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.common.api_response import api_response
from src.configs.app_configs import get_settings
from src.controllers.dependencies import get_current_user, require_admin
from src.cruds.strategy_score_crud import strategy_score_crud
from src.db.session import get_db
from src.services.insight.scoring.scorer import StrategyScorer

router = APIRouter(prefix="/api/strategy-scores", tags=["strategy-scores"])


def _to_float(v) -> float | None:
    return float(v) if v is not None else None


@router.get("")
@api_response()
def list_strategy_scores(
    window: str = Query(default="30d", max_length=10),
    account_id: int = Query(default=1, ge=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rows = strategy_score_crud.find_by_window(db, account_id=account_id, window=window)
    return [
        {
            "id": r.id,
            "strategy_mode": r.strategy_mode,
            "symbol": r.symbol,
            "regime": r.regime,
            "window": r.window,
            "win_rate": _to_float(r.win_rate),
            "pnl_sum": _to_float(r.pnl_sum),
            "max_drawdown": _to_float(r.max_drawdown),
            "sharpe": _to_float(r.sharpe),
            "false_breakout_rate": _to_float(r.false_breakout_rate),
            "regime_fit_score": _to_float(r.regime_fit_score),
            "sample_count": r.sample_count,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rows
    ]


@router.post("/generate")
@api_response()
def generate_strategy_scores(
    window_days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    """手动触发策略评分 (admin only)。"""
    settings = get_settings()
    n = StrategyScorer(db).score_window(
        trading_mode=settings.TRADING_MODE.value, window=f"{window_days}d", window_days=window_days,
    )
    db.commit()
    return {"message": "Strategy scores generated", "groups": n, "window": f"{window_days}d"}
