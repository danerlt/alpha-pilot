"""ExecutionGuard — spec §6.3 的 10 条规则链, 一票否决。

按顺序短路:
  1. 日亏损 ≤ -max_daily_loss_pct → REJECT (circuit_breaker)
  2. 连续亏损 ≥ max_consecutive_losses → REJECT (circuit_breaker)
  3. 可用 USDT 不足 → REJECT
  4. OPEN_LONG 且已有同币持仓 → REJECT
  5. position_size_pct > max_position_size_pct → REJECT
  6. 单笔风险 > max_single_risk_pct → REJECT
  7. SL 与当前价距离不在 [sl_atr_min_mult, sl_atr_max_mult] × ATR 区间 → REJECT
  8. R/R < min_rr_ratio → REJECT
  9. CHAOTIC regime + OPEN_LONG → DEGRADE → HOLD
 10. review_rejected → REJECT

每次调用都写 risk_events 审计行 (PASS / REJECT / DEGRADE 都写)。

Outbox 发布 (Plan 5 codereview I11):
  注入 outbox + decision_id (调用方知道) 后, REJECT 命中发布 decision.rejected,
  DEGRADE 命中发布 decision.degraded; PASS / HOLD 不发. decision_id 缺失 (None)
  时跳过 publish — 没有 ai_decisions 行可关联.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.services.events.contracts import DecisionDegraded, DecisionRejected
from src.services.events.outbox import OutboxWriter
from src.shared.enums import PositionStatus
from src.models.account_entity import RiskProfile
from src.models.position import Position
from src.models.risk_event import RiskEvent
from src.models.trade import Trade
from src.strategy.proposal import DecisionProposal

logger = logging.getLogger(__name__)


@dataclass
class GuardDecision:
    result: Literal["PASS", "REJECT", "DEGRADE"]
    reason: str
    modified_action: Literal["HOLD"] | None = None  # DEGRADE 时


class ExecutionGuard:
    def __init__(
        self,
        session: Session,
        *,
        risk_profile: RiskProfile,
        outbox: Optional[OutboxWriter] = None,
    ):
        self._session = session
        self._profile = risk_profile
        self._outbox = outbox

    def check(
        self,
        *,
        proposal: DecisionProposal,
        trading_mode: str,
        current_price: float,
        regime: str,
        available_usdt: float,
        daily_pnl: float,
        daily_pnl_pct: float,
        atr: float,
        review_rejected: bool = False,
        decision_id: int | None = None,
        trace_id: str | None = None,
    ) -> GuardDecision:
        """逐条规则检查; 命中即短路写审计 + 返回。"""
        self._cur_decision_id = decision_id  # _record 内部用
        self._cur_trading_mode = trading_mode
        self._cur_trace_id = trace_id or f"guard:{proposal.symbol}:{datetime.now(tz=timezone.utc).timestamp()}"

        # HOLD 直接 PASS, 不耗规则。
        if proposal.action == "HOLD":
            return self._record(proposal, "PASS", "hold_no_check")

        p = self._profile

        # 1. 日亏损熔断
        if daily_pnl_pct <= -float(p.max_daily_loss_pct):
            return self._record(
                proposal, "REJECT",
                f"circuit_breaker:daily_loss_pct={daily_pnl_pct:.4f}",
            )

        # 2. 连续亏损熔断 (今日最近 N 笔)
        from datetime import time, timedelta
        today_utc = datetime.now(tz=timezone.utc).date()
        start = datetime.combine(today_utc, time.min, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        recent = self._session.execute(
            select(Trade).where(
                Trade.account_id == proposal.account_id,
                Trade.closed_at >= start,
                Trade.closed_at < end,
            ).order_by(Trade.closed_at.desc()).limit(int(p.max_consecutive_losses))
        ).scalars().all()
        if len(recent) >= int(p.max_consecutive_losses) and all(float(t.pnl or 0) < 0 for t in recent):
            return self._record(
                proposal, "REJECT",
                f"circuit_breaker:consecutive_losses>={int(p.max_consecutive_losses)}",
            )

        # 仅 OPEN_LONG 才检查仓位/风险/SL/RR; CLOSE_LONG 直接进 9-10 条
        if proposal.action == "OPEN_LONG":
            size_pct = float(proposal.position_size_pct or 0.0)

            # 3. 可用余额校验
            need = available_usdt * size_pct
            if need <= 0 or available_usdt < need:
                return self._record(
                    proposal, "REJECT",
                    f"insufficient_balance:need={need:.2f} available={available_usdt:.2f}",
                )

            # 4. 已有同币持仓
            existing = self._session.execute(
                select(Position).where(
                    Position.account_id == proposal.account_id,
                    Position.trading_mode == trading_mode,
                    Position.symbol == proposal.symbol,
                    Position.status == PositionStatus.OPEN.value,
                )
            ).scalars().first()
            if existing is not None:
                return self._record(
                    proposal, "REJECT",
                    f"already_open:{proposal.symbol}",
                )

            # 5. 仓位上限
            if size_pct > float(p.max_position_size_pct):
                return self._record(
                    proposal, "REJECT",
                    f"oversize:{size_pct:.4f}>{float(p.max_position_size_pct):.4f}",
                )

            # 6. 单笔风险
            entry = proposal.entry_price or current_price
            sl = proposal.stop_loss
            if sl is None or entry <= 0:
                return self._record(
                    proposal, "REJECT", "missing_sl_or_entry",
                )
            risk_pct = abs(entry - sl) / entry * size_pct
            if risk_pct > float(p.max_single_risk_pct):
                return self._record(
                    proposal, "REJECT",
                    f"single_risk:{risk_pct:.4f}>{float(p.max_single_risk_pct):.4f}",
                )

            # 7. SL/ATR 距离
            if atr > 0:
                sl_distance = abs(entry - sl)
                if not (float(p.sl_atr_min_mult) * atr <= sl_distance <= float(p.sl_atr_max_mult) * atr):
                    return self._record(
                        proposal, "REJECT",
                        f"sl_distance_out_of_range:{sl_distance:.4f}",
                    )

            # 8. R/R 比
            tp = proposal.take_profit
            if tp is not None:
                reward = abs(tp - entry)
                risk = abs(entry - sl)
                if risk <= 0 or reward / risk < float(p.min_rr_ratio):
                    return self._record(
                        proposal, "REJECT",
                        f"poor_rr:{(reward/risk if risk>0 else 0):.2f}<{float(p.min_rr_ratio):.2f}",
                    )

        # 9. CHAOTIC + OPEN_LONG → DEGRADE
        if proposal.action == "OPEN_LONG" and regime == "chaotic":
            return self._record(
                proposal, "DEGRADE", "chaotic_regime", modified="HOLD",
            )

        # 10. ReviewCritic 已 reject
        if review_rejected:
            return self._record(proposal, "REJECT", "review_rejected")

        return self._record(proposal, "PASS", "all_checks_passed")

    def _record(
        self,
        proposal: DecisionProposal,
        result: str,
        reason: str,
        modified: str | None = None,
    ) -> GuardDecision:
        """写 risk_events + 视情况发 decision.degraded / decision.rejected + 返回 GuardDecision。"""
        self._session.add(RiskEvent(
            account_id=proposal.account_id,
            event_type=f"GUARD_{result}",
            symbol=proposal.symbol,
            triggered_at=datetime.now(tz=timezone.utc),
            description=reason,
            resolved=(result == "PASS"),
        ))
        self._session.flush()

        # publish 给 Notifier / UI: 只在有 outbox + decision_id 时发, PASS / HOLD 不发
        decision_id = getattr(self, "_cur_decision_id", None)
        if (
            self._outbox is not None
            and decision_id is not None
            and result in {"REJECT", "DEGRADE"}
        ):
            try:
                if result == "DEGRADE":
                    self._outbox.record(
                        self._session,
                        aggregate_type="ai_decision", aggregate_id=decision_id,
                        event=DecisionDegraded(
                            decision_id=decision_id,
                            original_action=proposal.action,
                            modified_action=modified or "HOLD",
                            reason=reason,
                        ),
                        account_id=proposal.account_id,
                        trading_mode=getattr(self, "_cur_trading_mode", "testnet"),
                        trace_id=getattr(self, "_cur_trace_id", "guard"),
                    )
                else:  # REJECT
                    self._outbox.record(
                        self._session,
                        aggregate_type="ai_decision", aggregate_id=decision_id,
                        event=DecisionRejected(
                            decision_id=decision_id,
                            reason=reason,
                        ),
                        account_id=proposal.account_id,
                        trading_mode=getattr(self, "_cur_trading_mode", "testnet"),
                        trace_id=getattr(self, "_cur_trace_id", "guard"),
                    )
            except Exception:
                # publish 失败不应阻塞 guard 决策
                logger.exception("guard outbox publish failed (non-fatal)")

        return GuardDecision(
            result=result,  # type: ignore[arg-type]
            reason=reason,
            modified_action=modified,  # type: ignore[arg-type]
        )
