"""ManualOpsService — 人工兜底操作 (spec §6.5)。

V0.1 提供:
  - manual_close_position: 单仓平仓 (跳过 Guard)
  - manual_close_all: 一键全平 (紧急通道, 跳过 Guard)
  - manual_resolve_circuit_breaker: 解除熝断
  - manual_open_long: 手动开多 (走 Guard, 但跳过 ReviewCritic)

每个动作都写 audit_logs (含 operator_user_id + reason) + 发
manual.override outbox 事件。
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.services.events.contracts import ManualOverride
from src.services.events.outbox import OutboxWriter
from src.core.exchange.adapter import ExchangeAdapter
from src.services.execution.order_executor import OrderExecutor
from src.common.enums import PositionStatus
from src.models.audit_log import AuditLog
from src.models.position import Position
from src.models.risk_event import RiskEvent
from src.models.trade import Trade

logger = logging.getLogger(__name__)


class ManualOpsService:
    def __init__(
        self,
        session: Session,
        adapter: ExchangeAdapter,
        outbox: Optional[OutboxWriter] = None,
    ):
        self._session = session
        self._adapter = adapter
        self._outbox = outbox

    def manual_close_position(
        self,
        *,
        position_id: int,
        reason: str,
        operator_user_id: int,
        trading_mode: str = "testnet",
    ) -> Trade | None:
        """关闭指定持仓。"""
        position = self._session.get(Position, position_id)
        if position is None or position.status != PositionStatus.OPEN.value:
            return None
        executor = OrderExecutor(self._session, self._adapter, outbox=self._outbox)
        trade = executor.close_long(
            position=position, reason=f"manual:{reason}",
            decision_id=None,
            account_id=position.account_id, trading_mode=position.trading_mode,
        )
        self._audit_and_emit(
            action="manual_close_position",
            operator_user_id=operator_user_id, reason=reason,
            target=str(position_id), account_id=position.account_id,
            trading_mode=position.trading_mode,
        )
        return trade

    def manual_close_all(
        self,
        *,
        account_id: int,
        trading_mode: str,
        reason: str,
        operator_user_id: int,
    ) -> list[int]:
        """紧急通道：一键平掉账户所有 OPEN 持仓。返回被平仓的 position_id 列表。"""
        positions = self._session.execute(
            select(Position).where(
                Position.account_id == account_id,
                Position.trading_mode == trading_mode,
                Position.status == PositionStatus.OPEN.value,
            )
        ).scalars().all()
        executor = OrderExecutor(self._session, self._adapter, outbox=self._outbox)
        closed: list[int] = []
        for pos in positions:
            trade = executor.close_long(
                position=pos, reason=f"manual_close_all:{reason}",
                decision_id=None,
                account_id=account_id, trading_mode=trading_mode,
            )
            if trade is not None:
                closed.append(pos.id)
        self._audit_and_emit(
            action="manual_close_all",
            operator_user_id=operator_user_id, reason=reason,
            target=f"account={account_id}",
            account_id=account_id, trading_mode=trading_mode,
            extra={"closed_positions": closed},
        )
        return closed

    def manual_resolve_circuit_breaker(
        self,
        *,
        risk_event_id: int,
        reason: str,
        operator_user_id: int,
    ) -> bool:
        """标记 risk_event resolved=True (解除熔断)。"""
        event = self._session.get(RiskEvent, risk_event_id)
        if event is None:
            return False
        event.resolved = True
        event.resolved_at = datetime.now(tz=timezone.utc)
        self._audit_and_emit(
            action="manual_resolve_circuit_breaker",
            operator_user_id=operator_user_id, reason=reason,
            target=str(risk_event_id),
            account_id=event.account_id, trading_mode=event.trading_mode,
        )
        self._session.flush()
        return True

    def _audit_and_emit(
        self, *,
        action: str, operator_user_id: int, reason: str,
        target: str, account_id: int, trading_mode: str,
        extra: dict | None = None,
    ) -> None:
        payload = {"reason": reason}
        if extra:
            payload.update(extra)
        self._session.add(AuditLog(
            account_id=account_id, user_id=operator_user_id,
            action=action, resource_type="manual_op", resource_id=target,
            after_json=payload,
        ))
        self._session.flush()
        if self._outbox is not None:
            self._outbox.record(
                self._session,
                aggregate_type="manual_op", aggregate_id=None,
                event=ManualOverride(
                    operator_user_id=operator_user_id,
                    action=action, target=target, reason=reason,
                ),
                account_id=account_id, trading_mode=trading_mode,
                trace_id=f"manual:{datetime.now(timezone.utc).timestamp()}",
            )
