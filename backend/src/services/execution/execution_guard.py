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

from src.common.enums import PositionStatus
from src.models.account_entity import RiskProfile
from src.models.position import Position
from src.models.risk_event import RiskEvent
from src.models.trade import Trade
from src.services.events.contracts import DecisionDegraded, DecisionRejected
from src.services.events.outbox import OutboxWriter
from src.services.strategy.proposal import DecisionProposal

logger = logging.getLogger(__name__)


@dataclass
class GuardDecision:
    result: Literal["PASS", "REJECT", "DEGRADE"]
    reason: str
    modified_action: Literal["HOLD"] | None = None  # DEGRADE 时


@dataclass
class GuardCheckResult:
    """单条守卫规则的逐项结果 (handoff P2 预检 UI 用)。"""

    check: str
    passed: bool
    note: str
    severity: Literal["REJECT", "DEGRADE"] = "REJECT"  # 未通过时的裁决级别


def derive_verdict(results: list[GuardCheckResult]) -> tuple[str, str]:
    """逐项结果 → (verdict, reason): 首个未通过项定裁决, 全过为 PASS。

    check() 与手动下单预检共用, 保证两条路径判定同源。
    """
    first_fail = next((r for r in results if not r.passed), None)
    if first_fail is None:
        return "PASS", "all_checks_passed"
    if first_fail.severity == "DEGRADE":
        return "DEGRADE", first_fail.note
    return "REJECT", first_fail.note


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
        """裁决入口: evaluate() 逐项结果 → 首个未通过项定裁决 → 写审计/发事件。

        handoff P2 重构: 判定逻辑单一实现在 evaluate(), 本方法只做裁决推导
        与副作用 (risk_events + outbox), 保证预检与实盘同一套规则。
        """
        self._cur_decision_id = decision_id  # _record 内部用
        self._cur_trading_mode = trading_mode
        self._cur_trace_id = trace_id or f"guard:{proposal.symbol}:{datetime.now(tz=timezone.utc).timestamp()}"

        # HOLD 直接 PASS, 不耗规则。
        if proposal.action == "HOLD":
            return self._record(proposal, "PASS", "hold_no_check")

        results = self.evaluate(
            proposal=proposal, trading_mode=trading_mode,
            current_price=current_price, regime=regime,
            available_usdt=available_usdt, daily_pnl=daily_pnl,
            daily_pnl_pct=daily_pnl_pct, atr=atr,
            review_rejected=review_rejected,
        )
        verdict, reason = derive_verdict(results)
        if verdict == "DEGRADE":
            return self._record(proposal, "DEGRADE", reason, modified="HOLD")
        return self._record(proposal, verdict, reason)

    def evaluate(
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
    ) -> list[GuardCheckResult]:
        """跑全部规则 (不短路、不写审计、不发事件), 按 1-10 顺序返回逐项结果。

        HOLD 返回空列表; 不适用的规则 passed=True 并在 note 说明。
        未通过项的 note 与旧版短路 reason 逐字一致 (审计/测试兼容)。
        """
        if proposal.action == "HOLD":
            return []

        p = self._profile
        is_open = proposal.action == "OPEN_LONG"
        results: list[GuardCheckResult] = []

        # 1. 日亏损熔断
        if daily_pnl_pct <= -float(p.max_daily_loss_pct):
            results.append(GuardCheckResult(
                "daily_loss", False,
                f"circuit_breaker:daily_loss_pct={daily_pnl_pct:.4f}",
            ))
        else:
            results.append(GuardCheckResult(
                "daily_loss", True, f"daily_pnl_pct={daily_pnl_pct:.4f}",
            ))

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
            results.append(GuardCheckResult(
                "consecutive_losses", False,
                f"circuit_breaker:consecutive_losses>={int(p.max_consecutive_losses)}",
            ))
        else:
            results.append(GuardCheckResult(
                "consecutive_losses", True,
                f"recent_losses<{int(p.max_consecutive_losses)}",
            ))

        # 3-8 仅 OPEN_LONG 适用; CLOSE_LONG 标 n/a
        size_pct = float(proposal.position_size_pct or 0.0)
        entry = proposal.entry_price or current_price
        sl = proposal.stop_loss
        sl_valid = sl is not None and entry > 0

        # 3. 可用余额
        if is_open:
            need = available_usdt * size_pct
            if need <= 0 or available_usdt < need:
                results.append(GuardCheckResult(
                    "balance", False,
                    f"insufficient_balance:need={need:.2f} available={available_usdt:.2f}",
                ))
            else:
                results.append(GuardCheckResult(
                    "balance", True, f"need={need:.2f} available={available_usdt:.2f}",
                ))
        else:
            results.append(GuardCheckResult("balance", True, "n/a (close order)"))

        # 4. 已有同币持仓
        if is_open:
            existing = self._session.execute(
                select(Position).where(
                    Position.account_id == proposal.account_id,
                    Position.trading_mode == trading_mode,
                    Position.symbol == proposal.symbol,
                    Position.status == PositionStatus.OPEN.value,
                )
            ).scalars().first()
            if existing is not None:
                results.append(GuardCheckResult(
                    "duplicate_position", False, f"already_open:{proposal.symbol}",
                ))
            else:
                results.append(GuardCheckResult(
                    "duplicate_position", True, "no open position",
                ))
        else:
            results.append(GuardCheckResult("duplicate_position", True, "n/a (close order)"))

        # 5. 仓位上限
        if is_open and size_pct > float(p.max_position_size_pct):
            results.append(GuardCheckResult(
                "position_size", False,
                f"oversize:{size_pct:.4f}>{float(p.max_position_size_pct):.4f}",
            ))
        else:
            results.append(GuardCheckResult(
                "position_size", True,
                f"size_pct={size_pct:.4f}" if is_open else "n/a (close order)",
            ))

        # 6. 单笔风险 (含 SL/entry 缺失)
        if is_open:
            if not sl_valid:
                results.append(GuardCheckResult("single_risk", False, "missing_sl_or_entry"))
            else:
                risk_pct = abs(entry - sl) / entry * size_pct
                if risk_pct > float(p.max_single_risk_pct):
                    results.append(GuardCheckResult(
                        "single_risk", False,
                        f"single_risk:{risk_pct:.4f}>{float(p.max_single_risk_pct):.4f}",
                    ))
                else:
                    results.append(GuardCheckResult(
                        "single_risk", True, f"risk_pct={risk_pct:.4f}",
                    ))
        else:
            results.append(GuardCheckResult("single_risk", True, "n/a (close order)"))

        # 7. SL/ATR 距离
        if is_open and sl_valid and atr > 0:
            sl_distance = abs(entry - sl)
            if not (float(p.sl_atr_min_mult) * atr <= sl_distance <= float(p.sl_atr_max_mult) * atr):
                results.append(GuardCheckResult(
                    "sl_distance", False,
                    f"sl_distance_out_of_range:{sl_distance:.4f}",
                ))
            else:
                results.append(GuardCheckResult(
                    "sl_distance", True, f"sl_distance={sl_distance:.4f}",
                ))
        else:
            results.append(GuardCheckResult(
                "sl_distance", True,
                "n/a (close order)" if not is_open else "skipped (no sl/atr)",
            ))

        # 8. R/R 比
        tp = proposal.take_profit
        if is_open and sl_valid and tp is not None:
            reward = abs(tp - entry)
            risk = abs(entry - sl)
            if risk <= 0 or reward / risk < float(p.min_rr_ratio):
                results.append(GuardCheckResult(
                    "rr_ratio", False,
                    f"poor_rr:{(reward/risk if risk>0 else 0):.2f}<{float(p.min_rr_ratio):.2f}",
                ))
            else:
                results.append(GuardCheckResult(
                    "rr_ratio", True, f"rr={reward/risk:.2f}",
                ))
        else:
            results.append(GuardCheckResult(
                "rr_ratio", True,
                "n/a (close order)" if not is_open else "skipped (no tp/sl)",
            ))

        # 9. CHAOTIC + OPEN_LONG → DEGRADE
        if is_open and regime == "chaotic":
            results.append(GuardCheckResult(
                "chaotic_regime", False, "chaotic_regime", severity="DEGRADE",
            ))
        else:
            results.append(GuardCheckResult("chaotic_regime", True, f"regime={regime}"))

        # 10. ReviewCritic 已 reject
        if review_rejected:
            results.append(GuardCheckResult("review", False, "review_rejected"))
        else:
            results.append(GuardCheckResult("review", True, "not rejected"))

        # 11. 策略启停 (风控页开关真实生效): 被禁用模式的 OPEN_LONG 拒绝
        from src.services.strategy.strategy_registry import get_disabled_modes

        if is_open and proposal.strategy_mode in get_disabled_modes(self._session):
            results.append(GuardCheckResult(
                "strategy_enabled", False,
                f"strategy_disabled:{proposal.strategy_mode}",
            ))
        else:
            results.append(GuardCheckResult(
                "strategy_enabled", True, f"mode={proposal.strategy_mode}",
            ))

        return results

    def _record(
        self,
        proposal: DecisionProposal,
        result: str,
        reason: str,
        modified: str | None = None,
    ) -> GuardDecision:
        """写 risk_events + 视情况发 decision.degraded / decision.rejected + 返回 GuardDecision。"""
        decision_id = getattr(self, "_cur_decision_id", None)
        self._session.add(RiskEvent(
            account_id=proposal.account_id,
            event_type=f"GUARD_{result}",
            symbol=proposal.symbol,
            triggered_at=datetime.now(tz=timezone.utc),
            description=reason,
            resolved=(result == "PASS"),
            decision_id=decision_id,
        ))
        self._session.flush()

        # publish 给 Notifier / UI: 只在有 outbox + decision_id 时发, PASS / HOLD 不发
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
