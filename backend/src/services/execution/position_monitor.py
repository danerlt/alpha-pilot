"""PositionMonitor — 10 秒循环刷新价格 + 止损/止盈触发 + 日亏损熔断 (spec §6.5)。

V0.1 不依赖 Binance 委托单 (止盈虽然挂在交易所, 但触发判定完全用 ticker
+ 数据库): SL 穿透立即市价平仓, TP 抵达立即市价平仓; 这两个动作走
OrderExecutor.close_long, 因此天然带 trace_id 幂等。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.common.enums import PositionStatus
from src.core.exchange.adapter import ExchangeAdapter
from src.models.position import Position
from src.models.risk_event import RiskEvent
from src.services.events.contracts import (
    CircuitBreakerTriggered,
    PositionUpdated,
)
from src.services.events.outbox import OutboxWriter
from src.services.execution.account_state import AccountStateService
from src.services.execution.order_executor import OrderExecutor
from src.services.risk.kill_switch import KillSwitchService

logger = logging.getLogger(__name__)


@dataclass
class MonitorResult:
    prices_updated: int = 0
    stop_loss_closed: list[int] = field(default_factory=list)
    take_profit_closed: list[int] = field(default_factory=list)
    circuit_breaker_triggered: bool = False


class PositionMonitor:
    def __init__(
        self,
        session: Session,
        adapter: ExchangeAdapter,
        executor: OrderExecutor,
        account_service: AccountStateService,
        outbox: OutboxWriter | None = None,
    ):
        self._session = session
        self._adapter = adapter
        self._executor = executor
        self._account = account_service
        self._outbox = outbox

    def run_once(
        self,
        *,
        account_id: int,
        trading_mode: str,
        max_daily_loss_pct: float = 0.03,
    ) -> MonitorResult:
        out = MonitorResult()

        positions = self._session.execute(
            select(Position).where(
                Position.account_id == account_id,
                Position.trading_mode == trading_mode,
                Position.status == PositionStatus.OPEN.value,
            )
        ).scalars().all()

        # 1. 刷新价格 + unrealized_pnl
        for pos in positions:
            try:
                ticker = self._adapter.get_ticker(pos.symbol)
                price = float(ticker.price)
            except Exception:
                logger.exception("ticker fetch failed for %s", pos.symbol)
                continue
            pos.current_price = price
            entry = float(pos.entry_price)
            qty = float(pos.quantity)
            pos.unrealized_pnl = (price - entry) * qty
            pos.unrealized_pnl_pct = (price - entry) / entry if entry > 0 else 0.0
            out.prices_updated += 1
            self._publish(
                aggregate_id=pos.id, account_id=account_id,
                trading_mode=trading_mode, aggregate_type="position",
                event=PositionUpdated(
                    position_id=pos.id, current_price=price,
                    unrealized_pnl=float(pos.unrealized_pnl),
                    unrealized_pnl_pct=float(pos.unrealized_pnl_pct),
                ),
            )
        self._session.flush()

        # 2. 止损检查
        for pos in positions:
            if pos.status != PositionStatus.OPEN.value:
                continue  # 上一轮可能已被平
            cur = float(pos.current_price or 0.0)
            if cur <= 0:
                continue
            sl = float(pos.stop_loss)
            if cur <= sl:
                self._record_risk_event(
                    account_id, trading_mode, pos.id, pos.symbol,
                    "STOP_LOSS_HIT",
                    f"price={cur:.4f} <= sl={sl:.4f}",
                )
                self._executor.close_long(
                    position=pos, reason="stop_loss",
                    decision_id=None,
                    account_id=account_id, trading_mode=trading_mode,
                )
                out.stop_loss_closed.append(pos.id)

        # 3. 止盈检查
        for pos in positions:
            if pos.status != PositionStatus.OPEN.value:
                continue
            tp = float(pos.take_profit) if pos.take_profit is not None else None
            cur = float(pos.current_price or 0.0)
            if tp is None or cur <= 0:
                continue
            if cur >= tp:
                self._executor.close_long(
                    position=pos, reason="take_profit",
                    decision_id=None,
                    account_id=account_id, trading_mode=trading_mode,
                )
                out.take_profit_closed.append(pos.id)

        # 4. 日亏损熔断检查
        _, daily_pnl_pct = self._account.get_daily_pnl(
            account_id=account_id, trading_mode=trading_mode,
        )
        if daily_pnl_pct <= -max_daily_loss_pct:
            # 去重 (post-Plan5 codereview Risk #1): 监控每 10s 一次, 一旦
            # daily_pnl_pct 持续低于阈值, 不去重会让今天写入几千条相同的
            # CIRCUIT_BREAKER_TRIGGERED, 操作员通过 /api/commands/resolve-breaker
            # 一次只能 resolve 一条 → 永远追不上, 熔断无法人工解除.
            already = KillSwitchService(self._session).has_unresolved_circuit_breaker(
                account_id=account_id, trading_mode=trading_mode,
            )
            if not already:
                self._record_risk_event(
                    account_id, trading_mode, None, None,
                    "CIRCUIT_BREAKER_TRIGGERED",
                    f"daily_pnl_pct={daily_pnl_pct:.4f}",
                )
                self._publish(
                    aggregate_id=None, account_id=account_id,
                    trading_mode=trading_mode, aggregate_type="risk",
                    event=CircuitBreakerTriggered(
                        reason=f"daily_loss:{daily_pnl_pct:.4f}",
                    ),
                )
            out.circuit_breaker_triggered = True

        return out

    def _record_risk_event(
        self, account_id, trading_mode, position_id, symbol,
        event_type, description,
    ):
        self._session.add(RiskEvent(
            account_id=account_id, trading_mode=trading_mode,
            event_type=event_type, symbol=symbol,
            triggered_at=datetime.now(tz=timezone.utc),
            description=description,
            position_id=position_id,
        ))
        self._session.flush()

    def _publish(
        self, *, aggregate_id, account_id, trading_mode, aggregate_type,
        event,
    ) -> None:
        if self._outbox is None:
            return
        self._outbox.record(
            self._session,
            aggregate_type=aggregate_type, aggregate_id=aggregate_id,
            event=event,
            account_id=account_id, trading_mode=trading_mode,
            trace_id=f"monitor:{datetime.now(tz=timezone.utc).timestamp()}",
        )
