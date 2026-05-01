"""执行守卫（风控校验）— PASS / REJECT / DEGRADE。

守卫规则（按优先级）：
1. 熔断状态检查（日亏损超限、连续亏损超限）→ REJECT
2. 已持仓时再次 OPEN_LONG → REJECT
3. 仓位上限检查 → REJECT / DEGRADE
4. 单笔风险检查（SL距离 * 仓位 > 账户 MAX_SINGLE_RISK_PCT）→ REJECT
5. CHAOTIC 市场状态 + OPEN_LONG → DEGRADE (降级为 HOLD)
6. PASS
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from sqlalchemy import cast, Date, func
from sqlalchemy.orm import Session

from src.services.decision_engine.parser import DecisionPayload
from src.shared.config import get_settings
from src.shared.enums import Action, GuardResult, PositionStatus, RegimeType
from src.models.position import Position
from src.models.trade import Trade

logger = logging.getLogger(__name__)


@dataclass
class GuardDecision:
    result: GuardResult
    reason: str
    modified_action: Action | None = None  # DEGRADE 时的降级动作


def check(
    db: Session,
    payload: DecisionPayload,
    current_price: float,
    regime: str,
    available_usdt: float,
    daily_pnl: float,
    daily_pnl_pct: float,
) -> GuardDecision:
    """
    对 AI 决策进行风控校验，返回 GuardDecision。
    调用方根据 result 决定是否执行 order。
    """
    settings = get_settings()
    action = payload.action

    # --- 规则 1: 日亏损熔断 ---
    if daily_pnl_pct <= -settings.MAX_DAILY_LOSS_PCT:
        logger.warning(
            "CIRCUIT BREAKER: daily_pnl_pct=%.4f exceeds limit=%.4f",
            daily_pnl_pct,
            settings.MAX_DAILY_LOSS_PCT,
        )
        return GuardDecision(
            result=GuardResult.REJECT,
            reason=f"circuit_breaker:daily_loss {daily_pnl_pct*100:.2f}% >= {settings.MAX_DAILY_LOSS_PCT*100:.2f}%",
        )

    # --- 规则 2: 连续亏损熔断 ---
    today = date.today()
    recent_trades = (
        db.query(Trade)
        .filter(
            Trade.trading_mode == settings.TRADING_MODE.value,
            cast(Trade.closed_at, Date) == today,
        )
        .order_by(Trade.closed_at.desc())
        .limit(settings.MAX_CONSECUTIVE_LOSSES)
        .all()
    )
    if len(recent_trades) >= settings.MAX_CONSECUTIVE_LOSSES:
        if all(float(t.pnl) < 0 for t in recent_trades):
            logger.warning("CIRCUIT BREAKER: %d consecutive losses", settings.MAX_CONSECUTIVE_LOSSES)
            return GuardDecision(
                result=GuardResult.REJECT,
                reason=f"circuit_breaker:consecutive_losses={settings.MAX_CONSECUTIVE_LOSSES}",
            )

    if action == Action.HOLD:
        return GuardDecision(result=GuardResult.PASS, reason="HOLD always passes")

    # --- 规则 3: OPEN_LONG 时检查是否已有同币持仓 ---
    if action == Action.OPEN_LONG:
        existing = (
            db.query(Position)
            .filter(
                Position.trading_mode == settings.TRADING_MODE.value,
                Position.symbol == payload.symbol,
                Position.status == PositionStatus.OPEN.value,
            )
            .first()
        )
        if existing:
            return GuardDecision(
                result=GuardResult.REJECT,
                reason=f"already_open_position:{payload.symbol}",
            )

    # --- 规则 4: 仓位上限 ---
    if action == Action.OPEN_LONG:
        pos_size_pct = payload.position_size_pct or 0.10
        if pos_size_pct > settings.MAX_POSITION_SIZE_PCT:
            return GuardDecision(
                result=GuardResult.REJECT,
                reason=f"position_size_pct {pos_size_pct:.2%} > limit {settings.MAX_POSITION_SIZE_PCT:.2%}",
            )

    # --- 规则 5: 单笔风险检查 ---
    if action == Action.OPEN_LONG and payload.stop_loss and payload.entry_price:
        risk_pct_per_unit = abs(payload.entry_price - payload.stop_loss) / payload.entry_price
        pos_size_pct = payload.position_size_pct or 0.10
        single_risk = risk_pct_per_unit * pos_size_pct
        if single_risk > settings.MAX_SINGLE_RISK_PCT:
            logger.warning(
                "Single trade risk %.4f exceeds limit %.4f",
                single_risk,
                settings.MAX_SINGLE_RISK_PCT,
            )
            return GuardDecision(
                result=GuardResult.REJECT,
                reason=f"single_risk {single_risk*100:.2f}% > limit {settings.MAX_SINGLE_RISK_PCT*100:.2f}%",
            )

    # --- 规则 6: CHAOTIC 市场 → DEGRADE OPEN_LONG ---
    if action == Action.OPEN_LONG and regime == RegimeType.CHAOTIC.value:
        logger.warning("DEGRADE: OPEN_LONG in CHAOTIC regime for %s", payload.symbol)
        return GuardDecision(
            result=GuardResult.DEGRADE,
            reason="chaotic_regime:degraded_to_hold",
            modified_action=Action.HOLD,
        )

    return GuardDecision(result=GuardResult.PASS, reason="all_checks_passed")
