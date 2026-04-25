"""OrderExecutor — open_long / close_long 幂等执行 (spec §6.4)。

trace_id 用 SHA256(decision_id:symbol:action) 截断 32 位作为幂等键, 写入
orders.trace_id (UNIQUE)。重复调用返回已存在的订单, 不重复下单。

下单后 sync_fill 一次, 写 positions / trades 行 + 发 order.* / position.* /
trade.* 事件。
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.events.contracts import (
    OrderFailed,
    OrderFilled,
    OrderSubmitted,
    PositionClosed,
    PositionOpened,
    TradeClosed,
)
from src.events.outbox import OutboxWriter
from src.execution.exchange.adapter import ExchangeAdapter
from src.execution.exchange.retry import (
    ExchangeTemporarilyUnavailable,
    PermanentExchangeError,
)
from src.execution.exchange.types import OrderRequest
from src.shared.enums import OrderStatus, PositionStatus
from src.shared.models.order import Order
from src.shared.models.position import Position
from src.shared.models.trade import Trade
from src.strategy.proposal import DecisionProposal

logger = logging.getLogger(__name__)


def make_trace_id(decision_id: int, symbol: str, action: str) -> str:
    raw = f"{decision_id}:{symbol}:{action}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


class OrderExecutor:
    def __init__(
        self,
        session: Session,
        adapter: ExchangeAdapter,
        outbox: Optional[OutboxWriter] = None,
    ):
        self._session = session
        self._adapter = adapter
        self._outbox = outbox

    # ----- OPEN LONG ----------------------------------------------------

    def open_long(
        self,
        *,
        proposal: DecisionProposal,
        decision_id: int,
        account_id: int,
        trading_mode: str,
        available_usdt: float,
        current_price: float,
    ) -> tuple[Order, Position] | None:
        """根据 proposal 开多仓。失败返回 None (内部已写 OrderFailed)。"""
        trace_id = make_trace_id(decision_id, proposal.symbol, "OPEN_LONG")

        # 幂等: trace_id 已存在 → 返回既有 (Order, Position)
        existing = self._session.execute(
            select(Order).where(Order.trace_id == trace_id)
        ).scalars().first()
        if existing is not None:
            pos = self._session.get(Position, existing.position_id) if existing.position_id else None
            return (existing, pos) if pos else None

        # 计算下单数量
        size_pct = float(proposal.position_size_pct or 0.10)
        notional = available_usdt * size_pct
        if current_price <= 0 or notional <= 0:
            return None
        quantity = round(notional / current_price, 8)

        request = OrderRequest(
            symbol=proposal.symbol,
            side="BUY",
            order_type=proposal.entry_type or "MARKET",
            quantity=quantity,
            price=proposal.entry_price if proposal.entry_type == "LIMIT" else None,
            client_order_id=trace_id,
        )

        order_row = Order(
            account_id=account_id,
            trading_mode=trading_mode,
            trace_id=trace_id,
            symbol=proposal.symbol,
            side="BUY",
            order_type=request.order_type,
            quantity=quantity,
            price=request.price,
            status=OrderStatus.PENDING.value,
            ai_decision_id=decision_id,
            submitted_at=datetime.now(tz=timezone.utc),
        )
        self._session.add(order_row)
        self._session.flush()

        try:
            result = self._adapter.submit_order(request)
        except (ExchangeTemporarilyUnavailable, PermanentExchangeError) as e:
            order_row.status = OrderStatus.FAILED.value
            order_row.error_message = str(e)[:500]
            self._session.flush()
            self._publish_outbox(
                aggregate_id=order_row.id, account_id=account_id,
                trading_mode=trading_mode, trace_id=trace_id,
                event=OrderFailed(order_id=order_row.id, reason=str(e)[:200]),
                aggregate_type="order",
            )
            logger.error("submit_order failed for trace_id=%s: %s", trace_id, e)
            return None

        # 同步填充字段
        order_row.binance_order_id = result.exchange_order_id
        order_row.status = result.status.lower() if result.status != "NEW" else OrderStatus.FILLED.value
        order_row.filled_quantity = result.filled_quantity
        order_row.avg_fill_price = result.avg_fill_price
        order_row.filled_at = datetime.now(tz=timezone.utc) if result.status == "FILLED" else None
        self._session.flush()

        # 发 order.submitted + order.filled
        self._publish_outbox(
            aggregate_id=order_row.id, account_id=account_id, trading_mode=trading_mode,
            trace_id=trace_id, aggregate_type="order",
            event=OrderSubmitted(
                order_id=order_row.id, symbol=proposal.symbol,
                side="BUY", order_type=request.order_type,
                quantity=quantity, price=request.price, trace_id=trace_id,
            ),
        )
        if result.status == "FILLED":
            self._publish_outbox(
                aggregate_id=order_row.id, account_id=account_id,
                trading_mode=trading_mode, trace_id=trace_id, aggregate_type="order",
                event=OrderFilled(
                    order_id=order_row.id, symbol=proposal.symbol,
                    filled_quantity=result.filled_quantity,
                    avg_fill_price=result.avg_fill_price or current_price,
                ),
            )

        # 写 Position
        position = Position(
            account_id=account_id,
            trading_mode=trading_mode,
            symbol=proposal.symbol,
            status=PositionStatus.OPEN.value,
            side="LONG",
            quantity=result.filled_quantity or quantity,
            entry_price=result.avg_fill_price or current_price,
            stop_loss=proposal.stop_loss,
            take_profit=proposal.take_profit,
            current_price=result.avg_fill_price or current_price,
            opened_at=datetime.now(tz=timezone.utc),
            ai_decision_id=decision_id,
        )
        self._session.add(position)
        self._session.flush()
        order_row.position_id = position.id
        self._session.flush()

        self._publish_outbox(
            aggregate_id=position.id, account_id=account_id,
            trading_mode=trading_mode, trace_id=trace_id, aggregate_type="position",
            event=PositionOpened(
                position_id=position.id, symbol=position.symbol,
                quantity=float(position.quantity),
                entry_price=float(position.entry_price),
                stop_loss=float(position.stop_loss),
                take_profit=float(position.take_profit) if position.take_profit else None,
            ),
        )

        return order_row, position

    # ----- CLOSE LONG ---------------------------------------------------

    def close_long(
        self,
        *,
        position: Position,
        reason: str,
        decision_id: int | None,
        account_id: int,
        trading_mode: str,
    ) -> Trade | None:
        """市价平仓。返回写入的 Trade 记录, 失败返回 None。"""
        trace_id = make_trace_id(
            decision_id or 0, position.symbol, f"CLOSE_LONG_{position.id}",
        )

        existing = self._session.execute(
            select(Order).where(Order.trace_id == trace_id)
        ).scalars().first()
        if existing is not None:
            return None  # 已平过, 不重复

        request = OrderRequest(
            symbol=position.symbol, side="SELL", order_type="MARKET",
            quantity=float(position.quantity), client_order_id=trace_id,
        )
        order_row = Order(
            account_id=account_id, trading_mode=trading_mode,
            trace_id=trace_id,
            symbol=position.symbol, side="SELL", order_type="MARKET",
            quantity=float(position.quantity),
            status=OrderStatus.PENDING.value,
            position_id=position.id,
            ai_decision_id=decision_id,
            submitted_at=datetime.now(tz=timezone.utc),
        )
        self._session.add(order_row)
        self._session.flush()

        try:
            result = self._adapter.submit_order(request)
        except (ExchangeTemporarilyUnavailable, PermanentExchangeError) as e:
            order_row.status = OrderStatus.FAILED.value
            order_row.error_message = str(e)[:500]
            self._session.flush()
            self._publish_outbox(
                aggregate_id=order_row.id, account_id=account_id,
                trading_mode=trading_mode, trace_id=trace_id, aggregate_type="order",
                event=OrderFailed(order_id=order_row.id, reason=str(e)[:200]),
            )
            return None

        exit_price = result.avg_fill_price or float(position.current_price or position.entry_price)
        order_row.binance_order_id = result.exchange_order_id
        order_row.status = OrderStatus.FILLED.value
        order_row.filled_quantity = result.filled_quantity
        order_row.avg_fill_price = exit_price
        order_row.filled_at = datetime.now(tz=timezone.utc)
        self._session.flush()

        # Position 标记 closed
        position.status = PositionStatus.CLOSED.value
        position.closed_at = datetime.now(tz=timezone.utc)
        position.current_price = exit_price
        self._session.flush()

        # Trade 记录
        entry = float(position.entry_price)
        qty = float(position.quantity)
        pnl = (exit_price - entry) * qty
        pnl_pct = (exit_price - entry) / entry if entry > 0 else 0.0
        # SQLite 不持久化 timezone, 读回来可能是 naive; 统一按 UTC 处理避免减法错。
        def _aware(dt):
            if dt is None:
                return datetime.now(tz=timezone.utc)
            return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
        opened_at = _aware(position.opened_at)
        closed_at = _aware(position.closed_at)
        holding_seconds = int((closed_at - opened_at).total_seconds()) if opened_at else 0

        trade = Trade(
            account_id=account_id, trading_mode=trading_mode,
            position_id=position.id, symbol=position.symbol, side="LONG",
            quantity=qty, entry_price=entry, exit_price=exit_price,
            pnl=pnl, pnl_pct=pnl_pct, exit_reason=reason,
            opened_at=opened_at, closed_at=closed_at,
            holding_seconds=holding_seconds,
            ai_decision_id=decision_id,
            close_order_id=order_row.id,
        )
        self._session.add(trade)
        self._session.flush()

        # 事件
        self._publish_outbox(
            aggregate_id=position.id, account_id=account_id,
            trading_mode=trading_mode, trace_id=trace_id, aggregate_type="position",
            event=PositionClosed(
                position_id=position.id, exit_price=exit_price,
                exit_reason=reason,
            ),
        )
        self._publish_outbox(
            aggregate_id=trade.id, account_id=account_id,
            trading_mode=trading_mode, trace_id=trace_id, aggregate_type="trade",
            event=TradeClosed(
                trade_id=trade.id, symbol=position.symbol,
                pnl=pnl, pnl_pct=pnl_pct, exit_reason=reason,
            ),
        )
        return trade

    # ----- 内部 ---------------------------------------------------------

    def _publish_outbox(
        self, *, aggregate_id, account_id, trading_mode, trace_id,
        event, aggregate_type: str,
    ) -> None:
        if self._outbox is None:
            return
        self._outbox.record(
            self._session,
            aggregate_type=aggregate_type, aggregate_id=aggregate_id,
            event=event,
            account_id=account_id, trading_mode=trading_mode, trace_id=trace_id,
        )
