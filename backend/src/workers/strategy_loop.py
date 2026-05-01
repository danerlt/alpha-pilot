"""策略循环 Worker — 每 15 分钟执行一次完整交易决策链。

链路：market_data → account_state → indicators → regime → experience_store
      → decision_engine → execution_guard → order_execution → reporting
      → Redis Pub/Sub
"""
from __future__ import annotations

import json
import logging
from typing import Any

import redis as redis_lib
from sqlalchemy.orm import Session

from src.services.account_state.service import (
    get_current_balance_usdt,
    get_daily_pnl,
    sync_account_snapshot,
)
from src.services.decision_engine.engine import make_decision
from src.services.execution_guard.guard import GuardDecision, check as guard_check
from src.services.experience_store.store import get_recent_experience
from src.services.indicators.calculator import compute_and_store, get_latest_indicators
from src.services.market_data.binance_client import get_symbol_ticker
from src.services.market_data.candle_service import SYMBOLS, TIMEFRAMES, fetch_and_store_candles
from src.services.order_execution.executor import close_long, open_long
from src.services.regime.classifier import classify_and_store, get_latest_regime
from src.shared.config import get_settings
from src.shared.enums import Action, GuardResult, PositionStatus
from src.models.position import Position
from src.models.risk_event import RiskEvent

logger = logging.getLogger(__name__)

# 主策略时间框架
PRIMARY_TIMEFRAME = "1h"


def _get_redis() -> redis_lib.Redis:
    settings = get_settings()
    return redis_lib.from_url(settings.REDIS_URL, decode_responses=True)


def _publish(r: redis_lib.Redis, channel: str, data: dict[str, Any]) -> None:
    try:
        r.publish(channel, json.dumps(data))
    except Exception as e:
        logger.error("Redis publish failed on channel %s: %s", channel, e)


def _is_circuit_broken(db: Session) -> bool:
    """检查今日是否存在未解除的熔断事件。"""
    settings = get_settings()
    from datetime import date
    from sqlalchemy import cast, Date
    event = (
        db.query(RiskEvent)
        .filter(
            RiskEvent.trading_mode == settings.TRADING_MODE.value,
            RiskEvent.event_type == "CIRCUIT_BREAKER_TRIGGERED",
            RiskEvent.resolved == False,
            cast(RiskEvent.triggered_at, Date) == date.today(),
        )
        .first()
    )
    return event is not None


def run_strategy_loop(db: Session) -> None:
    """执行一次完整策略循环（由 APScheduler 定期调用）。"""
    settings = get_settings()
    r = _get_redis()

    # 熔断检查
    if _is_circuit_broken(db):
        logger.warning("Strategy loop skipped: circuit breaker is active")
        return

    # Step 1: 拉取 K 线
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            try:
                fetch_and_store_candles(db, symbol, tf, limit=300)
            except Exception as e:
                logger.error("Failed to fetch candles %s %s: %s", symbol, tf, e)

    # Step 2: 同步账户状态
    try:
        sync_account_snapshot(db)
    except Exception as e:
        logger.error("Failed to sync account snapshot: %s", e)

    available_usdt = get_current_balance_usdt(db)
    daily_pnl, daily_pnl_pct = get_daily_pnl(db)

    # Step 3~4: 每个币种执行指标计算 + 市场状态识别 + 决策
    for symbol in SYMBOLS:
        _run_symbol_decision(
            db=db,
            r=r,
            symbol=symbol,
            timeframe=PRIMARY_TIMEFRAME,
            available_usdt=available_usdt,
            daily_pnl=daily_pnl,
            daily_pnl_pct=daily_pnl_pct,
        )

    logger.info("Strategy loop completed for %s", SYMBOLS)


def _run_symbol_decision(
    db: Session,
    r: redis_lib.Redis,
    symbol: str,
    timeframe: str,
    available_usdt: float,
    daily_pnl: float,
    daily_pnl_pct: float,
) -> None:
    settings = get_settings()

    # Step 3: 计算指标
    try:
        compute_and_store(db, symbol, timeframe)
    except Exception as e:
        logger.error("Indicator calculation failed %s %s: %s", symbol, timeframe, e)
        return

    # Step 4: 市场状态识别
    try:
        classify_and_store(db, symbol, timeframe)
    except Exception as e:
        logger.error("Regime classification failed %s %s: %s", symbol, timeframe, e)
        return

    # 获取最新指标和市场状态
    ind_snap = get_latest_indicators(db, symbol, timeframe)
    regime_snap = get_latest_regime(db, symbol, timeframe)

    if ind_snap is None or regime_snap is None:
        logger.warning("Missing indicator or regime snapshot for %s %s", symbol, timeframe)
        return

    # 当前价格
    try:
        ticker = get_symbol_ticker(symbol)
        current_price = float(ticker["price"])
    except Exception as e:
        logger.error("Failed to get ticker for %s: %s", symbol, e)
        return

    # 当前开仓持仓
    open_pos = (
        db.query(Position)
        .filter(
            Position.trading_mode == settings.TRADING_MODE.value,
            Position.symbol == symbol,
            Position.status == PositionStatus.OPEN.value,
        )
        .first()
    )
    open_pos_dict: dict | None = None
    if open_pos:
        open_pos_dict = {
            "symbol": open_pos.symbol,
            "quantity": float(open_pos.quantity),
            "entry_price": float(open_pos.entry_price),
            "stop_loss": float(open_pos.stop_loss),
            "take_profit": float(open_pos.take_profit) if open_pos.take_profit else None,
            "unrealized_pnl": float(open_pos.unrealized_pnl or 0),
        }

    # Step 5: 检索历史经验
    experience = get_recent_experience(db, symbol, limit=3)

    # 构建指标字典
    indicators_dict = {
        "ema20": float(ind_snap.ema20) if ind_snap.ema20 else None,
        "ema50": float(ind_snap.ema50) if ind_snap.ema50 else None,
        "ema200": float(ind_snap.ema200) if ind_snap.ema200 else None,
        "rsi": float(ind_snap.rsi) if ind_snap.rsi else None,
        "macd": float(ind_snap.macd) if ind_snap.macd else None,
        "macd_signal": float(ind_snap.macd_signal) if ind_snap.macd_signal else None,
        "macd_hist": float(ind_snap.macd_hist) if ind_snap.macd_hist else None,
        "atr": float(ind_snap.atr) if ind_snap.atr else None,
        "bb_upper": float(ind_snap.bb_upper) if ind_snap.bb_upper else None,
        "bb_middle": float(ind_snap.bb_middle) if ind_snap.bb_middle else None,
        "bb_lower": float(ind_snap.bb_lower) if ind_snap.bb_lower else None,
        "volume_ma": float(ind_snap.volume_ma) if ind_snap.volume_ma else None,
        "volatility": float(ind_snap.volatility) if ind_snap.volatility else None,
    }
    regime_dict = {
        "regime": regime_snap.regime,
        "confidence": float(regime_snap.confidence),
    }
    account_dict = {
        "available_usdt": available_usdt,
        "daily_pnl": daily_pnl,
        "daily_pnl_pct": daily_pnl_pct,
    }

    # Step 6: AI 决策
    try:
        payload, decision_record = make_decision(
            db=db,
            symbol=symbol,
            timeframe=timeframe,
            current_price=current_price,
            indicators=indicators_dict,
            regime=regime_dict,
            account=account_dict,
            open_position=open_pos_dict,
            recent_experience=experience,
        )
    except Exception as e:
        logger.error("Decision engine failed for %s: %s", symbol, e)
        return

    # Step 7: 执行守卫
    try:
        guard: GuardDecision = guard_check(
            db=db,
            payload=payload,
            current_price=current_price,
            regime=regime_snap.regime,
            available_usdt=available_usdt,
            daily_pnl=daily_pnl,
            daily_pnl_pct=daily_pnl_pct,
        )
    except Exception as e:
        logger.error("Execution guard failed for %s: %s", symbol, e)
        return

    # Step 8: 下单执行
    if guard.result == GuardResult.REJECT:
        logger.info("Order REJECTED for %s: %s", symbol, guard.reason)
        _publish(r, "trading_events", {
            "type": "guard_reject", "symbol": symbol, "reason": guard.reason,
        })
        return

    effective_action = guard.modified_action if guard.result == GuardResult.DEGRADE else payload.action

    if effective_action == Action.OPEN_LONG:
        try:
            result = open_long(db, payload, decision_record.id)
            if result:
                order, position = result
                _publish(r, "trading_events", {
                    "type": "position_opened",
                    "symbol": symbol,
                    "position_id": position.id,
                    "entry_price": float(position.entry_price),
                    "quantity": float(position.quantity),
                    "stop_loss": float(position.stop_loss),
                })
        except Exception as e:
            logger.error("Order execution failed for %s: %s", symbol, e)

    elif effective_action == Action.CLOSE_LONG and open_pos:
        from src.shared.enums import TradeExitReason
        try:
            close_long(db, open_pos, TradeExitReason.AI_CLOSE, decision_record.id)
            _publish(r, "trading_events", {
                "type": "position_closed",
                "symbol": symbol,
                "reason": "ai_close",
            })
        except Exception as e:
            logger.error("Close long failed for %s: %s", symbol, e)

    # Publish decision event
    _publish(r, "trading_events", {
        "type": "decision",
        "symbol": symbol,
        "action": effective_action.value,
        "confidence": payload.confidence,
        "regime": regime_snap.regime,
        "is_fallback": payload.is_fallback,
    })
