"""持仓监控服务 — 止损检测、止盈轮询、日亏损熔断。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.services.market_data.binance_client import get_order, get_symbol_ticker
from src.services.order_execution.executor import close_long
from src.shared.config import get_settings
from src.shared.enums import OrderStatus, PositionStatus, TradeExitReason
from src.models.order import Order
from src.models.position import Position
from src.models.risk_event import RiskEvent

logger = logging.getLogger(__name__)


def _log_risk_event(
    db: Session,
    event_type: str,
    description: str,
    symbol: str | None = None,
    position_id: int | None = None,
) -> None:
    settings = get_settings()
    event = RiskEvent(
        trading_mode=settings.TRADING_MODE.value,
        event_type=event_type,
        symbol=symbol,
        triggered_at=datetime.now(tz=timezone.utc),
        description=description,
        position_id=position_id,
    )
    db.add(event)
    db.commit()
    logger.warning("Risk event [%s]: %s", event_type, description)


def update_position_prices(db: Session) -> None:
    """更新所有开仓持仓的当前价格和未实现 PnL。"""
    settings = get_settings()
    open_positions = (
        db.query(Position)
        .filter(
            Position.trading_mode == settings.TRADING_MODE.value,
            Position.status == PositionStatus.OPEN.value,
        )
        .all()
    )
    for pos in open_positions:
        try:
            ticker = get_symbol_ticker(pos.symbol)
            current = float(ticker["price"])
            entry = float(pos.entry_price)
            qty = float(pos.quantity)
            pnl = (current - entry) * qty
            pnl_pct = (current - entry) / entry if entry > 0 else 0.0
            pos.current_price = current
            pos.unrealized_pnl = pnl
            pos.unrealized_pnl_pct = pnl_pct
        except Exception as e:
            logger.error("Failed to update price for position %d: %s", pos.id, e)
    db.commit()


def check_stop_losses(db: Session) -> list[int]:
    """检查所有开仓是否触发止损，触发则市价平仓。返回被平仓的 position_id 列表。"""
    settings = get_settings()
    closed_ids: list[int] = []
    open_positions = (
        db.query(Position)
        .filter(
            Position.trading_mode == settings.TRADING_MODE.value,
            Position.status == PositionStatus.OPEN.value,
        )
        .all()
    )
    for pos in open_positions:
        current = float(pos.current_price or 0)
        sl = float(pos.stop_loss)
        if current <= 0:
            continue
        if current <= sl:
            logger.warning(
                "Stop loss triggered: %s pos_id=%d current=%.4f sl=%.4f",
                pos.symbol, pos.id, current, sl,
            )
            _log_risk_event(
                db,
                "STOP_LOSS_HIT",
                f"{pos.symbol} price {current:.4f} crossed SL {sl:.4f}",
                symbol=pos.symbol,
                position_id=pos.id,
            )
            close_long(db, pos, TradeExitReason.STOP_LOSS)
            closed_ids.append(pos.id)
    return closed_ids


def check_take_profits(db: Session) -> list[int]:
    """
    轮询止盈委托单状态。
    若已成交，关闭持仓并写入 trades。
    返回被平仓的 position_id 列表。
    """
    settings = get_settings()
    closed_ids: list[int] = []
    open_positions = (
        db.query(Position)
        .filter(
            Position.trading_mode == settings.TRADING_MODE.value,
            Position.status == PositionStatus.OPEN.value,
            Position.take_profit.isnot(None),
        )
        .all()
    )
    for pos in open_positions:
        current = float(pos.current_price or 0)
        tp = float(pos.take_profit)
        if current >= tp:
            logger.info(
                "Take profit reached: %s pos_id=%d current=%.4f tp=%.4f",
                pos.symbol, pos.id, current, tp,
            )
            close_long(db, pos, TradeExitReason.TAKE_PROFIT)
            closed_ids.append(pos.id)
    return closed_ids


def check_daily_loss_circuit_breaker(db: Session, daily_pnl_pct: float) -> bool:
    """
    检查日亏损是否超限，超限则记录熔断事件。
    返回 True 表示熔断已触发。
    """
    settings = get_settings()
    if daily_pnl_pct <= -settings.MAX_DAILY_LOSS_PCT:
        _log_risk_event(
            db,
            "CIRCUIT_BREAKER_TRIGGERED",
            f"Daily loss {daily_pnl_pct*100:.2f}% exceeded limit {settings.MAX_DAILY_LOSS_PCT*100:.2f}%",
        )
        return True
    return False


def run_monitor_cycle(db: Session, daily_pnl_pct: float) -> dict:
    """
    执行一次完整持仓监控循环。
    返回结果摘要。
    """
    update_position_prices(db)
    sl_closed = check_stop_losses(db)
    tp_closed = check_take_profits(db)
    circuit_broken = check_daily_loss_circuit_breaker(db, daily_pnl_pct)

    return {
        "stop_loss_closed": sl_closed,
        "take_profit_closed": tp_closed,
        "circuit_breaker_triggered": circuit_broken,
    }
