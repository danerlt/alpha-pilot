"""ShadowRunner — 影子执行 + 模拟评估 + 灰度自动回滚 (handoff 3.5)。

V1 采用 **mirror 模式**: 对 SHADOW 候选, 以主管道最新真实决策为基线,
应用候选 params_json 的参数变换生成影子 proposal, 写 shadow_decisions
(**不下单**); 评估轮用当前价对影子 proposal 模拟 PnL (pct 口径) 写
shadow_evaluations, 与线上实际逐笔对比。
真·独立 LLM 决策链 (每候选独立跑 prompt→solve→review) 留 V2。

params_json 支持的变换 (无该键则不变换):
  sl_mult:   SL 距离倍数   sl' = entry - (entry-sl)×sl_mult
  tp_mult:   TP 距离倍数   tp' = entry + (tp-entry)×tp_mult
  size_scale: 仓位缩放     size' = min(size×scale, 1.0)
  min_confidence: 置信度门槛, proposal.confidence < 门槛 → 改 HOLD

灰度自动回滚: CANARY 候选在日亏达到熔断上限的 80% 时自动 ROLLED_BACK
(比全局熔断更保守 — 新策略问题要早于全账户熔断被叫停) + lab.update 事件。
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.cruds.lab_candidate_crud import lab_candidate_crud
from src.models.decision import AIDecision
from src.models.shadow import ShadowDecision, ShadowEvaluation
from src.models.trade import Trade
from src.services.events.outbox import OutboxWriter
from src.services.lab.lab_service import LabService

logger = logging.getLogger(__name__)

_LOOKBACK_MINUTES = 45  # 只镜像最近一轮主管道的决策 (15m 周期 ×3 容错)
CANARY_ROLLBACK_FRACTION = 0.8


def transform_proposal(base: dict, params: dict) -> dict:
    """mirror 变换: 真实决策 → 候选参数下的影子 proposal。纯函数。"""
    out = dict(base)
    entry = out.get("entry_price")
    sl = out.get("stop_loss")
    tp = out.get("take_profit")
    if entry and sl and params.get("sl_mult"):
        out["stop_loss"] = round(entry - (entry - sl) * float(params["sl_mult"]), 8)
    if entry and tp and params.get("tp_mult"):
        out["take_profit"] = round(entry + (tp - entry) * float(params["tp_mult"]), 8)
    if out.get("position_size_pct") and params.get("size_scale"):
        out["position_size_pct"] = min(
            round(out["position_size_pct"] * float(params["size_scale"]), 6), 1.0,
        )
    min_conf = params.get("min_confidence")
    if (
        min_conf is not None
        and out.get("action") == "OPEN_LONG"
        and float(out.get("confidence") or 0) < float(min_conf)
    ):
        out["action"] = "HOLD"
        out["hold_reason"] = f"confidence<{min_conf}"
    return out


def simulate_pnl_pct(proposal: dict, current_price: float) -> float | None:
    """OPEN_LONG 影子 proposal 的模拟 PnL (pct×size 口径); 其他动作返回 None。"""
    if proposal.get("action") != "OPEN_LONG":
        return None
    entry = proposal.get("entry_price")
    if not entry or current_price <= 0:
        return None
    sl = proposal.get("stop_loss")
    tp = proposal.get("take_profit")
    size = float(proposal.get("position_size_pct") or 0.1)
    if sl and current_price <= sl:
        raw = (sl - entry) / entry
    elif tp and current_price >= tp:
        raw = (tp - entry) / entry
    else:
        raw = (current_price - entry) / entry
    return round(raw * size, 8)


class ShadowRunner:
    def __init__(self, session: Session, adapter, outbox: OutboxWriter | None = None):
        self._session = session
        self._adapter = adapter
        self._outbox = outbox

    def run_once(self, *, trading_mode: str, account_id: int = 1) -> dict:
        """镜像最新真实决策 + 评估既有影子行 + 灰度回滚检查。返回统计。"""
        mirrored = self._mirror_recent_decisions(trading_mode=trading_mode, account_id=account_id)
        evaluated = self._evaluate_pending(trading_mode=trading_mode)
        rolled_back = self._check_canary_rollback(trading_mode=trading_mode, account_id=account_id)
        self._session.commit()
        return {"mirrored": mirrored, "evaluated": evaluated, "rolled_back": rolled_back}

    # ── 镜像 ────────────────────────────────────────────────────────────

    def _mirror_recent_decisions(self, *, trading_mode: str, account_id: int) -> int:
        candidates = lab_candidate_crud.find_by_stage(
            self._session, ["SHADOW"], trading_mode=trading_mode,
        )
        if not candidates:
            return 0
        since = datetime.now(tz=timezone.utc) - timedelta(minutes=_LOOKBACK_MINUTES)
        recent = list(self._session.execute(
            select(AIDecision).where(
                AIDecision.trading_mode == trading_mode,
                AIDecision.account_id == account_id,
                AIDecision.source == "ai_trader",
                AIDecision.decided_at >= since,
            )
        ).scalars())
        count = 0
        for cand in candidates:
            for d in recent:
                # 幂等: 同 run 同真实决策只镜像一次
                exists = self._session.execute(
                    select(ShadowDecision.id).where(
                        ShadowDecision.shadow_run_id == cand.shadow_run_id,
                        ShadowDecision.real_decision_id == d.id,
                    )
                ).scalars().first()
                if exists:
                    continue
                base = {
                    "symbol": d.symbol,
                    "action": d.action,
                    "confidence": float(d.confidence) if d.confidence else None,
                    "entry_price": float(d.entry_price) if d.entry_price else None,
                    "stop_loss": float(d.stop_loss) if d.stop_loss else None,
                    "take_profit": float(d.take_profit) if d.take_profit else None,
                    "position_size_pct": float(d.position_size_pct) if d.position_size_pct else None,
                }
                self._session.add(ShadowDecision(
                    shadow_run_id=cand.shadow_run_id,
                    real_decision_id=d.id,
                    proposal_json=transform_proposal(base, cand.params_json or {}),
                ))
                count += 1
        self._session.flush()
        return count

    # ── 评估 ────────────────────────────────────────────────────────────

    def _evaluate_pending(self, *, trading_mode: str) -> int:
        """对活跃影子 run 的 shadow_decisions 逐条 (重)评估模拟 PnL。"""
        active = lab_candidate_crud.find_by_stage(
            self._session, ["SHADOW", "CANARY"], trading_mode=trading_mode,
        )
        run_ids = [c.shadow_run_id for c in active if c.shadow_run_id]
        if not run_ids:
            return 0
        rows = list(self._session.execute(
            select(ShadowDecision).where(ShadowDecision.shadow_run_id.in_(run_ids))
        ).scalars())
        prices: dict[str, float] = {}
        count = 0
        for sd in rows:
            proposal = sd.proposal_json or {}
            symbol = proposal.get("symbol")
            if not symbol:
                continue
            if symbol not in prices:
                try:
                    prices[symbol] = float(self._adapter.get_ticker(symbol).price)
                except Exception:  # noqa: BLE001
                    logger.warning("shadow eval: ticker failed for %s", symbol, exc_info=True)
                    continue
            sim = simulate_pnl_pct(proposal, prices[symbol])
            if sim is None:
                continue
            real_pnl = self._real_pnl_for(sd.real_decision_id)
            existing = self._session.execute(
                select(ShadowEvaluation).where(
                    ShadowEvaluation.shadow_decision_id == sd.id,
                )
            ).scalars().first()
            if existing is None:
                self._session.add(ShadowEvaluation(
                    shadow_decision_id=sd.id,
                    shadow_pnl_sim=sim, real_pnl=real_pnl,
                    diff=(sim - real_pnl) if real_pnl is not None else None,
                    evaluated_at=datetime.now(tz=timezone.utc),
                ))
            else:
                existing.shadow_pnl_sim = sim
                existing.real_pnl = real_pnl
                existing.diff = (sim - real_pnl) if real_pnl is not None else None
                existing.evaluated_at = datetime.now(tz=timezone.utc)
            count += 1
        self._session.flush()
        return count

    def _real_pnl_for(self, real_decision_id: int | None) -> float | None:
        if real_decision_id is None:
            return None
        trade = self._session.execute(
            select(Trade).where(Trade.ai_decision_id == real_decision_id)
        ).scalars().first()
        return float(trade.pnl_pct) if trade is not None and trade.pnl_pct is not None else None

    # ── 灰度自动回滚 ─────────────────────────────────────────────────────

    def _check_canary_rollback(self, *, trading_mode: str, account_id: int) -> int:
        canaries = lab_candidate_crud.find_by_stage(
            self._session, ["CANARY"], trading_mode=trading_mode,
        )
        if not canaries:
            return 0
        from src.cruds.account_crud import account_snapshot_crud
        from src.cruds.account_entity_crud import risk_profile_crud

        snap = account_snapshot_crud.find_latest(
            self._session, trading_mode=trading_mode, account_id=account_id,
        )
        profile = risk_profile_crud.find_active(self._session, account_id=account_id)
        if snap is None or profile is None:
            return 0
        daily_pnl_pct = float(snap.daily_pnl_pct)
        threshold = -float(profile.max_daily_loss_pct) * CANARY_ROLLBACK_FRACTION
        if daily_pnl_pct > threshold:
            return 0
        count = 0
        svc = LabService(self._session, outbox=self._outbox)
        for cand in canaries:
            svc.rollback(
                candidate_id=cand.id,
                reason=f"canary_drawdown:{daily_pnl_pct:.4f}<={threshold:.4f}",
                trading_mode=trading_mode,
            )
            logger.warning("canary auto-rollback: candidate=%d daily_pnl_pct=%.4f", cand.id, daily_pnl_pct)
            count += 1
        return count
