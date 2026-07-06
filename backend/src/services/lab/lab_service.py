"""LabService — 策略实验室候选生命周期 (handoff 3.5)。

受控进化流水线: QUEUED → SHADOW → CANARY → LIVE
                          ↘ RETIRED (terminate)   CANARY ↘ ROLLED_BACK (自动回滚)

promote 门槛在服务端校验 (前端绕不过): 影子期进度 ≥60% 且影子模拟收益优于
线上基线且有足够样本。history 时间线复用 audit_logs (resource_type=lab_candidate)。
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.common.exception.errors import ServiceException
from src.cruds.lab_candidate_crud import lab_candidate_crud
from src.models.audit_log import AuditLog
from src.models.lab_candidate import LabCandidate
from src.models.shadow import ShadowDecision, ShadowEvaluation
from src.models.trade import Trade
from src.services.events.contracts import LabUpdate
from src.services.events.outbox import OutboxWriter

logger = logging.getLogger(__name__)

PROMOTE_MIN_PROGRESS = 0.6
PROMOTE_MIN_SHADOW_DECISIONS = 3


class LabService:
    def __init__(self, session: Session, outbox: Optional[OutboxWriter] = None):
        self._session = session
        self._outbox = outbox

    # ── 生命周期 ────────────────────────────────────────────────────────

    def submit(
        self, *, name: str, description: str | None, params: dict,
        trading_mode: str, user_id: int, source: str = "manual",
        shadow_days_target: int = 14,
    ) -> LabCandidate:
        row = lab_candidate_crud.add(
            self._session,
            trading_mode=trading_mode, name=name, description=description,
            source=source, params_json=params, stage="QUEUED",
            shadow_days_target=shadow_days_target, created_by=user_id,
        )
        self._audit_and_emit(row, action="lab_submit", user_id=user_id)
        self._session.commit()
        return row

    def start_shadow(self, *, candidate_id: int, user_id: int, trading_mode: str) -> LabCandidate:
        row = self._get_checked(candidate_id, trading_mode)
        if row.stage != "QUEUED":
            raise ServiceException(f"候选 stage={row.stage}, 仅 QUEUED 可开始影子运行")
        row.stage = "SHADOW"
        row.shadow_run_id = uuid.uuid4().hex
        row.shadow_started_at = datetime.now(tz=timezone.utc)
        self._session.flush()
        self._audit_and_emit(row, action="lab_start", user_id=user_id)
        self._session.commit()
        return row

    def promote(self, *, candidate_id: int, user_id: int, trading_mode: str) -> LabCandidate:
        """SHADOW→CANARY 需门槛; CANARY→LIVE 直接放行 (皆需 admin, 由 controller 守卫)。"""
        row = self._get_checked(candidate_id, trading_mode)
        if row.stage == "SHADOW":
            self._assert_promote_gate(row)
            row.stage = "CANARY"
        elif row.stage == "CANARY":
            row.stage = "LIVE"
        else:
            raise ServiceException(f"候选 stage={row.stage}, 不可 promote")
        row.promoted_by = user_id
        row.promoted_at = datetime.now(tz=timezone.utc)
        self._session.flush()
        self._audit_and_emit(row, action="lab_promote", user_id=user_id)
        self._session.commit()
        return row

    def terminate(self, *, candidate_id: int, user_id: int, trading_mode: str, reason: str = "") -> LabCandidate:
        row = self._get_checked(candidate_id, trading_mode)
        if row.stage in ("RETIRED", "ROLLED_BACK"):
            raise ServiceException(f"候选已归档 (stage={row.stage})")
        row.stage = "RETIRED"
        row.terminated_at = datetime.now(tz=timezone.utc)
        row.rollback_reason = reason or None
        self._session.flush()
        self._audit_and_emit(row, action="lab_retire", user_id=user_id, reason=reason)
        self._session.commit()
        return row

    def rollback(self, *, candidate_id: int, reason: str, trading_mode: str) -> LabCandidate:
        """灰度自动回滚 (调度器调用, operator=system/0)。"""
        row = self._get_checked(candidate_id, trading_mode)
        if row.stage != "CANARY":
            raise ServiceException(f"候选 stage={row.stage}, 仅 CANARY 可回滚")
        row.stage = "ROLLED_BACK"
        row.terminated_at = datetime.now(tz=timezone.utc)
        row.rollback_reason = reason
        self._session.flush()
        self._audit_and_emit(row, action="lab_rollback", user_id=0, reason=reason)
        self._session.commit()
        return row

    # ── 查询 ────────────────────────────────────────────────────────────

    def list_candidates(self, *, trading_mode: str) -> list[dict]:
        rows = lab_candidate_crud.find_all(self._session, trading_mode=trading_mode)
        return [self.candidate_detail(row) for row in rows]

    def candidate_detail(self, row: LabCandidate) -> dict:
        progress = self.shadow_progress(row)
        return {
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "source": row.source,
            "stage": row.stage,
            "params": row.params_json,
            "shadow_progress": progress,
            "shadow_days_target": row.shadow_days_target,
            "shadow_started_at": row.shadow_started_at.isoformat() if row.shadow_started_at else None,
            "promote_eligible": self._promote_gate_reason(row) is None,
            "promote_blocked_reason": self._promote_gate_reason(row),
            "metrics": self.compare_metrics(row),
            "rollback_reason": row.rollback_reason,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    def shadow_progress(self, row: LabCandidate) -> float:
        if row.shadow_started_at is None:
            return 0.0
        started = row.shadow_started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        elapsed_days = (datetime.now(tz=timezone.utc) - started).total_seconds() / 86400
        return min(1.0, elapsed_days / max(row.shadow_days_target, 1))

    def compare_metrics(self, row: LabCandidate) -> dict:
        """影子 vs 线上逐项对比 (交易数/净收益/胜率)。影子收益为模拟值 (pct 口径)。"""
        shadow = {"decisions": 0, "simulated_pnl_pct": 0.0, "win_rate": None}
        if row.shadow_run_id:
            decision_ids = list(self._session.execute(
                select(ShadowDecision.id).where(
                    ShadowDecision.shadow_run_id == row.shadow_run_id,
                )
            ).scalars())
            shadow["decisions"] = len(decision_ids)
            if decision_ids:
                evals = list(self._session.execute(
                    select(ShadowEvaluation).where(
                        ShadowEvaluation.shadow_decision_id.in_(decision_ids),
                    )
                ).scalars())
                pnls = [float(e.shadow_pnl_sim) for e in evals if e.shadow_pnl_sim is not None]
                if pnls:
                    shadow["simulated_pnl_pct"] = sum(pnls)
                    shadow["win_rate"] = sum(1 for p in pnls if p > 0) / len(pnls)

        live = {"trades": 0, "net_pnl_pct": 0.0, "win_rate": None}
        if row.shadow_started_at is not None:
            trades = list(self._session.execute(
                select(Trade).where(
                    Trade.trading_mode == row.trading_mode,
                    Trade.closed_at >= row.shadow_started_at,
                )
            ).scalars())
            live["trades"] = len(trades)
            if trades:
                pnls = [float(t.pnl_pct or 0) for t in trades]
                live["net_pnl_pct"] = sum(pnls)
                live["win_rate"] = sum(1 for p in pnls if p > 0) / len(pnls)
        return {"shadow": shadow, "live": live}

    def history(self, *, trading_mode: str, limit: int = 50) -> list[dict]:
        rows = list(self._session.execute(
            select(AuditLog).where(
                AuditLog.resource_type == "lab_candidate",
            ).order_by(AuditLog.id.desc()).limit(limit)
        ).scalars())
        return [
            {
                "action": r.action.removeprefix("lab_"),
                "candidate_id": int(r.resource_id) if r.resource_id else None,
                "candidate_name": (r.after_json or {}).get("name"),
                "stage": (r.after_json or {}).get("stage"),
                "reason": (r.after_json or {}).get("reason"),
                "operator": "system" if r.user_id == 0 else str(r.user_id),
                "at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    # ── 内部 ────────────────────────────────────────────────────────────

    def _assert_promote_gate(self, row: LabCandidate) -> None:
        reason = self._promote_gate_reason(row)
        if reason:
            raise ServiceException(f"promote 门槛未达标: {reason}")

    def _promote_gate_reason(self, row: LabCandidate) -> str | None:
        """SHADOW→CANARY 的门槛; 非 SHADOW 阶段返回对应说明。"""
        if row.stage != "SHADOW":
            return None if row.stage == "CANARY" else f"stage={row.stage} 不可申请灰度"
        progress = self.shadow_progress(row)
        if progress < PROMOTE_MIN_PROGRESS:
            return f"影子期进度 {progress:.0%} < {PROMOTE_MIN_PROGRESS:.0%}"
        metrics = self.compare_metrics(row)
        if metrics["shadow"]["decisions"] < PROMOTE_MIN_SHADOW_DECISIONS:
            return f"影子样本 {metrics['shadow']['decisions']} < {PROMOTE_MIN_SHADOW_DECISIONS}"
        if metrics["shadow"]["simulated_pnl_pct"] <= metrics["live"]["net_pnl_pct"]:
            return "影子模拟收益未优于线上基线"
        return None

    def _get_checked(self, candidate_id: int, trading_mode: str) -> LabCandidate:
        row = lab_candidate_crud.get(self._session, candidate_id)
        if row.trading_mode != trading_mode:
            raise ServiceException("候选不属于当前 trading_mode")
        return row

    def _audit_and_emit(
        self, row: LabCandidate, *, action: str, user_id: int, reason: str = "",
    ) -> None:
        self._session.add(AuditLog(
            account_id=1, user_id=user_id, action=action,
            resource_type="lab_candidate", resource_id=str(row.id),
            after_json={"name": row.name, "stage": row.stage, "reason": reason or None},
        ))
        self._session.flush()
        if self._outbox is not None:
            self._outbox.record(
                self._session,
                aggregate_type="lab_candidate", aggregate_id=row.id,
                event=LabUpdate(candidate_id=row.id, stage=row.stage, reason=reason or None),
                account_id=1, trading_mode=row.trading_mode,
                trace_id=f"lab:{row.id}:{action}",
            )
