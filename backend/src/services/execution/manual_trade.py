"""ManualTradeService — 手动下单预检/下单/改SLTP (handoff P2 §3.2)。

原则: 人工单与 AI 单走同一 ExecutionGuard 规则 (guard.evaluate 逐项 +
derive_verdict 同源裁决); HALTED 时仅放行 SELL + reduce_only 平仓单。
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from src.common.enums import PositionStatus
from src.common.exception.errors import RiskRejectedException, ServiceException
from src.core.exchange.adapter import ExchangeAdapter
from src.core.trace.trace_id import generate_manual_trace_id
from src.cruds.account_crud import account_snapshot_crud
from src.cruds.account_entity_crud import risk_profile_crud
from src.cruds.indicator_crud import indicator_snapshot_crud
from src.cruds.order_crud import order_crud
from src.cruds.position_crud import position_crud
from src.cruds.regime_crud import regime_snapshot_crud
from src.models.audit_log import AuditLog
from src.models.order import Order
from src.models.position import Position
from src.schemas.manual_order import ManualOrderCreate
from src.services.events.contracts import ManualOverride
from src.services.events.outbox import OutboxWriter
from src.services.execution.execution_guard import (
    ExecutionGuard,
    GuardCheckResult,
    derive_verdict,
)
from src.services.execution.order_executor import OrderExecutor
from src.services.risk.kill_switch import KillSwitchService
from src.services.strategy.proposal import DecisionProposal

logger = logging.getLogger(__name__)


@dataclass
class PrecheckOutcome:
    verdict: str  # PASS | REJECT | DEGRADE
    halted: bool
    checks: list[GuardCheckResult]
    context: dict = field(default_factory=dict)
    proposal: DecisionProposal | None = None
    position: Position | None = None  # SELL 时的目标持仓

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "halted": self.halted,
            "checks": [
                {"check": c.check, "pass": c.passed, "note": c.note}
                for c in self.checks
            ],
            "context": self.context,
        }


class ManualTradeService:
    def __init__(
        self,
        session: Session,
        adapter: ExchangeAdapter,
        outbox: Optional[OutboxWriter] = None,
    ):
        self._session = session
        self._adapter = adapter
        self._outbox = outbox

    def precheck(
        self,
        *,
        body: ManualOrderCreate,
        trading_mode: str,
        account_id: int = 1,
    ) -> PrecheckOutcome:
        """逐项守卫预检; 只读, 不写审计不发事件 (下单时服务端再跑一遍)。"""
        halted = KillSwitchService(self._session).should_block_new_trades(
            account_id=account_id, trading_mode=trading_mode,
        )
        is_reduce_close = body.side == "SELL" and body.reduce_only

        checks: list[GuardCheckResult] = []
        # kill_switch 永远是第一项 (handoff: HALTED 时仅接受 reduce_only)
        if halted and not is_reduce_close:
            checks.append(GuardCheckResult(
                "kill_switch", False, "halted: only reduce-only close allowed",
            ))
        elif halted:
            checks.append(GuardCheckResult(
                "kill_switch", True, "halted (reduce-only close allowed)",
            ))
        else:
            checks.append(GuardCheckResult("kill_switch", True, "not halted"))

        current_price = float(self._adapter.get_ticker(body.symbol).price)
        snap = account_snapshot_crud.find_latest(
            self._session, trading_mode=trading_mode, account_id=account_id,
        )
        available = float(snap.available_balance_usdt) if snap else 0.0
        daily_pnl = float(snap.daily_pnl) if snap else 0.0
        daily_pnl_pct = float(snap.daily_pnl_pct) if snap else 0.0
        ind = indicator_snapshot_crud.find_latest_by_symbol(
            self._session, trading_mode=trading_mode,
            symbol=body.symbol, account_id=account_id,
        )
        atr = float(ind.atr) if ind is not None and ind.atr is not None else 0.0
        regime_row = regime_snapshot_crud.find_latest_by_symbol(
            self._session, trading_mode=trading_mode,
            symbol=body.symbol, account_id=account_id,
        )
        regime = regime_row.regime if regime_row else "unknown"

        position: Position | None = None
        proposal: DecisionProposal | None = None
        entry_price = body.price or current_price
        notional = body.qty * entry_price

        if body.side == "SELL":
            position = self._find_open_position(
                trading_mode=trading_mode, symbol=body.symbol, account_id=account_id,
            )
            if position is None:
                checks.append(GuardCheckResult(
                    "position_exists", False, f"no open position for {body.symbol}",
                ))
            else:
                checks.append(GuardCheckResult(
                    "position_exists", True, f"position_id={position.id}",
                ))
                if abs(body.qty - float(position.quantity)) > 1e-8:
                    checks.append(GuardCheckResult(
                        "close_quantity", False,
                        f"partial close not supported in V0.1: "
                        f"qty={body.qty} position={float(position.quantity)}",
                    ))
                else:
                    checks.append(GuardCheckResult(
                        "close_quantity", True, f"qty={body.qty}",
                    ))
                proposal = DecisionProposal(
                    account_id=account_id, symbol=body.symbol, timeframe="manual",
                    action="CLOSE_LONG", confidence=1.0,
                    strategy_mode="manual", source="manual",
                )
        else:  # BUY → OPEN_LONG
            size_pct_raw = (notional / available) if available > 0 else float("inf")
            balance_overflow = size_pct_raw > 1.0
            proposal = DecisionProposal(
                account_id=account_id, symbol=body.symbol, timeframe="manual",
                action="OPEN_LONG", confidence=1.0,
                entry_type=body.type, entry_price=entry_price,
                stop_loss=body.sl, take_profit=body.tp,
                position_size_pct=min(size_pct_raw, 1.0),
                strategy_mode="manual", source="manual",
            )
            if balance_overflow:
                # size_pct 被 Pydantic 上限截到 1.0, guard 的 balance 规则测不出
                # 超额, 这里显式给出真实的 insufficient_balance 结果。
                checks.append(GuardCheckResult(
                    "balance", False,
                    f"insufficient_balance:need={notional:.2f} available={available:.2f}",
                ))

        if proposal is not None:
            guard = self._build_guard(account_id=account_id)
            guard_results = guard.evaluate(
                proposal=proposal, trading_mode=trading_mode,
                current_price=current_price, regime=regime,
                available_usdt=available, daily_pnl=daily_pnl,
                daily_pnl_pct=daily_pnl_pct, atr=atr,
            )
            existing = {c.check for c in checks}
            checks.extend(r for r in guard_results if r.check not in existing)

        verdict, _ = derive_verdict(checks)
        return PrecheckOutcome(
            verdict=verdict, halted=halted, checks=checks,
            context={
                "current_price": current_price,
                "available_usdt": available,
                "atr": atr,
                "regime": regime,
            },
            proposal=proposal, position=position,
        )

    # ------------------------------------------------------------------

    def place_order(
        self,
        *,
        body: ManualOrderCreate,
        trading_mode: str,
        operator_user_id: int,
        account_id: int = 1,
    ) -> dict:
        """手动下单: 服务端重跑守卫 (不信任预检结果) + 幂等 + 审计。

        本方法负责 commit (含失败订单行的持久化)。
        """
        if body.type == "LIMIT":
            raise ServiceException("LIMIT 暂不支持: V0.1 手动单为市价 + 监控式 SL/TP")

        client_order_id = body.client_order_id or uuid.uuid4().hex[:32]
        trace_id = generate_manual_trace_id(operator_user_id, client_order_id)

        # 幂等: 同 trace_id 直接返回既有订单
        existing = order_crud.get_by_trace_id(self._session, trace_id)
        if existing is not None:
            return self._order_summary(existing, trade_id=None)

        outcome = self.precheck(
            body=body, trading_mode=trading_mode, account_id=account_id,
        )
        if outcome.verdict != "PASS":
            first_fail = next(c for c in outcome.checks if not c.passed)
            raise RiskRejectedException(f"{first_fail.check}:{first_fail.note}")

        executor = OrderExecutor(self._session, self._adapter, outbox=self._outbox)
        if body.side == "BUY":
            res = executor.manual_open(
                proposal=outcome.proposal, quantity=body.qty, trace_id=trace_id,
                account_id=account_id, trading_mode=trading_mode,
                current_price=float(outcome.context["current_price"]),
            )
            if res is None:
                self._session.commit()  # 持久化 FAILED 订单行 + order.failed 事件
                raise ServiceException("手动开仓失败 (交易所异常), 详见 orders 表 error_message")
            order_row, position = res
            summary = self._order_summary(order_row, trade_id=None)
            summary["position_id"] = position.id
        else:
            trade = executor.close_long(
                position=outcome.position, reason="manual",
                decision_id=None,
                account_id=account_id, trading_mode=trading_mode,
                trace_id=trace_id,
            )
            if trade is None:
                self._session.commit()
                raise ServiceException("手动平仓失败 (交易所异常), 详见 orders 表 error_message")
            order_row = order_crud.get_by_trace_id(self._session, trace_id)
            summary = self._order_summary(order_row, trade_id=trade.id)
            summary["position_id"] = outcome.position.id

        self._audit(
            operator_user_id=operator_user_id, account_id=account_id,
            trading_mode=trading_mode, body=body, trace_id=trace_id,
        )
        self._session.commit()
        return summary

    @staticmethod
    def _order_summary(order: Order | None, *, trade_id: int | None) -> dict:
        return {
            "order_id": order.id if order else None,
            "trace_id": order.trace_id if order else None,
            "status": order.status if order else None,
            "position_id": order.position_id if order else None,
            "trade_id": trade_id,
        }

    def _audit(
        self, *, operator_user_id: int, account_id: int,
        trading_mode: str, body: ManualOrderCreate, trace_id: str,
    ) -> None:
        """审计行 + manual.override 事件 (与 ManualOpsService 同模式)。"""
        detail = {
            "symbol": body.symbol, "side": body.side, "qty": body.qty,
            "sl": body.sl, "tp": body.tp, "reduce_only": body.reduce_only,
        }
        self._session.add(AuditLog(
            account_id=account_id, user_id=operator_user_id,
            action="manual_order", resource_type="order", resource_id=trace_id,
            after_json=detail,
        ))
        self._session.flush()
        if self._outbox is not None:
            self._outbox.record(
                self._session,
                aggregate_type="manual_op", aggregate_id=None,
                event=ManualOverride(
                    operator_user_id=operator_user_id,
                    action="manual_order", target=f"{body.symbol}:{body.side}",
                    reason=f"trace_id={trace_id}",
                ),
                account_id=account_id, trading_mode=trading_mode,
                trace_id=trace_id,
            )

    def _build_guard(self, *, account_id: int) -> ExecutionGuard:
        profile = risk_profile_crud.find_active(self._session, account_id=account_id)
        if profile is None:
            raise ServiceException(f"no active risk_profile for account_id={account_id}")
        return ExecutionGuard(self._session, risk_profile=profile)

    def _find_open_position(
        self, *, trading_mode: str, symbol: str, account_id: int,
    ) -> Position | None:
        rows = position_crud.find_by_status(self._session, [PositionStatus.OPEN.value])
        for p in rows:
            if (
                p.account_id == account_id
                and p.trading_mode == trading_mode
                and p.symbol == symbol
            ):
                return p
        return None
