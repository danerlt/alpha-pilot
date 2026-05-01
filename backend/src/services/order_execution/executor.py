"""下单执行服务 — 幂等开仓/平仓，trace_id 防重复下单。"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from src.services.decision_engine.parser import DecisionPayload
from src.services.market_data.binance_client import (
    cancel_order,
    create_order,
    get_order,
    get_symbol_ticker,
)
from src.shared.config import get_settings
from src.shared.enums import Action, EntryType, OrderStatus, PositionStatus, TradeExitReason
from src.models.order import Order
from src.models.position import Position
from src.models.trade import Trade

logger = logging.getLogger(__name__)


def _make_trace_id(decision_id: int, symbol: str, action: str) -> str:
    raw = f"{decision_id}:{symbol}:{action}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _get_current_price(symbol: str) -> float:
    ticker = get_symbol_ticker(symbol)
    return float(ticker["price"])


def _sync_order_fill(db: Session, order: Order) -> Order:
    """从 Binance 拉取订单状态并同步到 DB。"""
    if not order.binance_order_id:
        return order
    try:
        raw = get_order(order.symbol, int(order.binance_order_id))
        status_map = {
            "FILLED": OrderStatus.FILLED,
            "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
            "CANCELED": OrderStatus.CANCELLED,
            "CANCELLED": OrderStatus.CANCELLED,
            "REJECTED": OrderStatus.FAILED,
            "EXPIRED": OrderStatus.CANCELLED,
        }
        new_status = status_map.get(raw.get("status", ""), None)
        if new_status:
            order.status = new_status.value
        order.filled_quantity = float(raw.get("executedQty", 0))
        avg = raw.get("cummulativeQuoteQty", 0)
        filled_qty = float(raw.get("executedQty", 0))
        if filled_qty > 0 and float(avg) > 0:
            order.avg_fill_price = float(avg) / filled_qty
        if new_status == OrderStatus.FILLED:
            order.filled_at = datetime.now(tz=timezone.utc)
        db.commit()
    except Exception as e:
        logger.error("Failed to sync order %s from Binance: %s", order.binance_order_id, e)
    return order


def open_long(
    db: Session,
    payload: DecisionPayload,
    decision_id: int,
) -> tuple[Order, Position] | None:
    """
    执行开多仓。
    1. 幂等检查（trace_id）
    2. Binance 下单
    3. 写入 orders + positions
    返回 (Order, Position)，失败返回 None。
    """
    settings = get_settings()
    trace_id = _make_trace_id(decision_id, payload.symbol, "OPEN_LONG")

    # 幂等检查
    existing = db.query(Order).filter(Order.trace_id == trace_id).first()
    if existing:
        logger.warning("Duplicate order detected, trace_id=%s, skipping", trace_id)
        pos = db.query(Position).filter(Position.id == existing.position_id).first()
        return (existing, pos) if pos else None

    current_price = _get_current_price(payload.symbol)
    pos_size_pct = payload.position_size_pct or 0.10

    # 计算下单数量
    balance = (
        db.query(__import__("src.models.account", fromlist=["AccountSnapshot"]).AccountSnapshot)
        .filter_by(trading_mode=settings.TRADING_MODE.value)
        .order_by(
            __import__("src.models.account", fromlist=["AccountSnapshot"]).AccountSnapshot.snapshot_at.desc()
        )
        .first()
    )
    available_usdt = float(balance.available_balance_usdt) if balance else 0.0
    order_usdt = available_usdt * pos_size_pct
    entry_price = payload.entry_price or current_price
    quantity = round(order_usdt / entry_price, 6)

    if quantity <= 0:
        logger.error("Calculated quantity is 0 for %s", payload.symbol)
        return None

    # 下单
    order_kwargs: dict[str, Any] = {
        "quantity": quantity,
        "newClientOrderId": trace_id,
    }
    if payload.entry_type == EntryType.LIMIT and payload.entry_price:
        order_kwargs["price"] = str(payload.entry_price)
        order_kwargs["timeInForce"] = "GTC"
        binance_type = "LIMIT"
    else:
        binance_type = "MARKET"

    try:
        raw_order = create_order(
            symbol=payload.symbol,
            side="BUY",
            order_type=binance_type,
            **order_kwargs,
        )
        logger.info("Order placed: %s BUY %s qty=%s", binance_type, payload.symbol, quantity)
    except Exception as e:
        logger.error("Failed to place BUY order for %s: %s", payload.symbol, e)
        order_rec = Order(
            trading_mode=settings.TRADING_MODE.value,
            trace_id=trace_id,
            symbol=payload.symbol,
            side="BUY",
            order_type=binance_type,
            quantity=quantity,
            price=payload.entry_price,
            status=OrderStatus.FAILED.value,
            ai_decision_id=decision_id,
            submitted_at=datetime.now(tz=timezone.utc),
            error_message=str(e)[:500],
        )
        db.add(order_rec)
        db.commit()
        return None

    filled_qty = float(raw_order.get("executedQty", quantity))
    avg_price = entry_price
    cumulative_quote = raw_order.get("cummulativeQuoteQty")
    if cumulative_quote and filled_qty > 0:
        avg_price = float(cumulative_quote) / filled_qty

    binance_status = raw_order.get("status", "")
    status = OrderStatus.FILLED if binance_status == "FILLED" else OrderStatus.PENDING

    # 写入 Position
    position = Position(
        trading_mode=settings.TRADING_MODE.value,
        symbol=payload.symbol,
        status=PositionStatus.OPEN.value,
        side="LONG",
        quantity=filled_qty,
        entry_price=avg_price,
        stop_loss=payload.stop_loss or avg_price * 0.98,
        take_profit=payload.take_profit,
        current_price=avg_price,
        unrealized_pnl=0.0,
        unrealized_pnl_pct=0.0,
        opened_at=datetime.now(tz=timezone.utc),
        ai_decision_id=decision_id,
    )
    db.add(position)
    db.flush()  # get position.id

    # 写入 Order
    order_rec = Order(
        trading_mode=settings.TRADING_MODE.value,
        trace_id=trace_id,
        binance_order_id=str(raw_order.get("orderId", "")),
        symbol=payload.symbol,
        side="BUY",
        order_type=binance_type,
        quantity=quantity,
        price=payload.entry_price,
        filled_quantity=filled_qty,
        avg_fill_price=avg_price,
        status=status.value,
        position_id=position.id,
        ai_decision_id=decision_id,
        submitted_at=datetime.now(tz=timezone.utc),
        filled_at=datetime.now(tz=timezone.utc) if status == OrderStatus.FILLED else None,
    )
    db.add(order_rec)
    db.commit()
    db.refresh(position)
    db.refresh(order_rec)
    logger.info("Position opened: id=%d %s qty=%.6f entry=%.4f SL=%.4f", position.id, payload.symbol, filled_qty, avg_price, position.stop_loss)
    return order_rec, position


def close_long(
    db: Session,
    position: Position,
    exit_reason: TradeExitReason,
    decision_id: int | None = None,
) -> Order | None:
    """
    市价平仓指定 Position，写入 trades 记录。
    返回平仓 Order。
    """
    settings = get_settings()
    trace_id = _make_trace_id(
        decision_id or position.id,
        position.symbol,
        f"CLOSE_LONG_{position.id}",
    )

    existing = db.query(Order).filter(Order.trace_id == trace_id).first()
    if existing:
        logger.warning("Duplicate close order trace_id=%s", trace_id)
        return existing

    current_price = _get_current_price(position.symbol)
    qty = float(position.quantity)

    try:
        raw_order = create_order(
            symbol=position.symbol,
            side="SELL",
            order_type="MARKET",
            quantity=qty,
            newClientOrderId=trace_id,
        )
    except Exception as e:
        logger.error("Failed to close position %d: %s", position.id, e)
        order_rec = Order(
            trading_mode=settings.TRADING_MODE.value,
            trace_id=trace_id,
            symbol=position.symbol,
            side="SELL",
            order_type="MARKET",
            quantity=qty,
            status=OrderStatus.FAILED.value,
            position_id=position.id,
            ai_decision_id=decision_id,
            submitted_at=datetime.now(tz=timezone.utc),
            error_message=str(e)[:500],
        )
        db.add(order_rec)
        db.commit()
        return None

    filled_qty = float(raw_order.get("executedQty", qty))
    cumulative_quote = raw_order.get("cummulativeQuoteQty")
    exit_price = current_price
    if cumulative_quote and filled_qty > 0:
        exit_price = float(cumulative_quote) / filled_qty

    now = datetime.now(tz=timezone.utc)
    entry_price = float(position.entry_price)
    pnl = (exit_price - entry_price) * filled_qty
    pnl_pct = (exit_price - entry_price) / entry_price if entry_price > 0 else 0.0
    holding_seconds = int((now - position.opened_at).total_seconds())

    # 更新 Position
    position.status = PositionStatus.CLOSED.value
    position.current_price = exit_price
    position.unrealized_pnl = 0.0
    position.closed_at = now

    # 写入 Order
    order_rec = Order(
        trading_mode=settings.TRADING_MODE.value,
        trace_id=trace_id,
        binance_order_id=str(raw_order.get("orderId", "")),
        symbol=position.symbol,
        side="SELL",
        order_type="MARKET",
        quantity=qty,
        filled_quantity=filled_qty,
        avg_fill_price=exit_price,
        status=OrderStatus.FILLED.value,
        position_id=position.id,
        ai_decision_id=decision_id,
        submitted_at=now,
        filled_at=now,
    )
    db.add(order_rec)
    db.flush()

    # 写入 Trade
    trade = Trade(
        trading_mode=settings.TRADING_MODE.value,
        position_id=position.id,
        symbol=position.symbol,
        side="LONG",
        quantity=filled_qty,
        entry_price=entry_price,
        exit_price=exit_price,
        pnl=pnl,
        pnl_pct=pnl_pct,
        exit_reason=exit_reason.value,
        opened_at=position.opened_at,
        closed_at=now,
        holding_seconds=holding_seconds,
        ai_decision_id=decision_id,
        close_order_id=order_rec.id,
    )
    db.add(trade)
    db.commit()
    logger.info(
        "Position closed: id=%d %s exit=%.4f pnl=%.4f (%.2f%%) reason=%s",
        position.id, position.symbol, exit_price, pnl, pnl_pct * 100, exit_reason.value,
    )
    return order_rec
