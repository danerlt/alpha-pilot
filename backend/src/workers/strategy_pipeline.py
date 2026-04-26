"""strategy_pipeline worker — 一次完整决策循环 (spec §3.4)。

按 account_id × symbol × timeframe 串起 Part A/B/C：
  1. MarketDataService.fetch_and_store
  2. IndicatorComputer.compute
  3. FactorComputer.compute_and_store
  4. RegimeClassifier.classify_and_store
  5. (前置) KillSwitchService.should_block_new_trades —— 整账户级
  6. AccountStateService.sync_snapshot
  7. 查 open_position
  8. StrategyRouter.decide → DecisionProposal
  9. ExecutionGuard.check → GuardDecision
 10. 按 Guard 结果: PASS+OPEN_LONG → OrderExecutor.open_long;
                  PASS+CLOSE_LONG → close_long;
                  DEGRADE/REJECT → 不下单, 仅记录

代码组织 (Plan 5 codereview I3):
  run_strategy_pipeline_once 只负责装配服务 / 检查 KillSwitch / 同步账户快照 /
  逐 symbol×tf 调用 _run_one_symbol_tf; 单币种异常吃掉 + 写日志保单轮幂等.
  _run_one_symbol_tf 处理一个币种的全链路, 不再涉及循环 / 异常吞噬。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.control.kill_switch.service import KillSwitchService
from src.events.contracts import (
    DecisionProposed,
    FactorsUpdated,
    IndicatorsComputed,
    RegimeClassified,
)
from src.events.outbox import OutboxWriter
from src.execution.account.state import AccountStateService
from src.execution.exchange.adapter import ExchangeAdapter
from src.execution.guard.execution_guard import ExecutionGuard
from src.execution.market.data import MarketDataService
from src.execution.orders.executor import OrderExecutor
from src.insight.experience.retriever import ExperienceRetriever
from src.insight.factors.computer import FactorComputer
from src.insight.indicators.computer import IndicatorComputer
from src.insight.regime.classifier import RegimeClassifier
from src.shared.enums import PositionStatus
from src.shared.models.account_entity import RiskProfile
from src.shared.models.candle import Candle
from src.shared.models.position import Position
from src.strategy.ai_trader.decision_solver import DecisionSolver
from src.strategy.ai_trader.llm_client import LLMClient
from src.strategy.ai_trader.pipeline import AITraderPipeline, PipelineInput
from src.strategy.ai_trader.prompt_composer import PromptComposer
from src.strategy.ai_trader.review_critic import ReviewCritic
from src.strategy.router import StrategyRouter

logger = logging.getLogger(__name__)


def _candles_df_for(session, *, account_id, trading_mode, symbol, timeframe, limit=210) -> pd.DataFrame:
    """从 DB 拉最近 limit 根 K 线 → time-forward DataFrame。"""
    rows = session.execute(
        select(Candle).where(
            Candle.account_id == account_id,
            Candle.trading_mode == trading_mode,
            Candle.symbol == symbol,
            Candle.timeframe == timeframe,
        ).order_by(Candle.open_time.desc()).limit(limit)
    ).scalars().all()
    rows = list(reversed(rows))
    if not rows:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    return pd.DataFrame({
        "open_time": [c.open_time for c in rows],
        "open": [float(c.open) for c in rows],
        "high": [float(c.high) for c in rows],
        "low": [float(c.low) for c in rows],
        "close": [float(c.close) for c in rows],
        "volume": [float(c.volume) for c in rows],
    }).set_index("open_time")


@dataclass
class _PipelineDeps:
    """单次 cycle 内要共享给 _run_one_symbol_tf 的服务装配."""
    market: MarketDataService
    indicator: IndicatorComputer
    factor_computer: FactorComputer
    regime_classifier: RegimeClassifier
    router: StrategyRouter
    guard: ExecutionGuard
    executor: OrderExecutor
    adapter: ExchangeAdapter
    outbox: Optional[OutboxWriter]


def _run_one_symbol_tf(
    *,
    db: Session,
    account_id: int,
    trading_mode: str,
    symbol: str,
    tf: str,
    deps: _PipelineDeps,
    available_usdt: float,
    daily_pnl: float,
    daily_pnl_pct: float,
) -> dict:
    """跑一个 symbol×timeframe 的完整决策链, 返回 summary item.

    本函数只负责"业务流"; 异常吞噬 / commit / rollback 留给 caller, 让
    每个 symbol 的事务边界清晰。
    """
    trace_id = f"pipeline:{symbol}:{tf}:{datetime.now(timezone.utc).timestamp()}"

    # 1. 拉 K 线
    deps.market.fetch_and_store(
        account_id=account_id, trading_mode=trading_mode,
        symbol=symbol, timeframe=tf,
        trace_id=trace_id, limit=210,
    )

    # 2. 算指标
    values, snap_id = deps.indicator.compute(
        account_id=account_id, trading_mode=trading_mode,
        symbol=symbol, timeframe=tf, limit=210,
    )
    if not values.is_valid_for_trading():
        return {"action": "SKIP", "reason": "insufficient_indicators"}

    # 3. 算因子
    df = _candles_df_for(
        db, account_id=account_id, trading_mode=trading_mode,
        symbol=symbol, timeframe=tf, limit=210,
    )
    latest_open_time = (
        df.index[-1].to_pydatetime() if not df.empty else datetime.now(timezone.utc)
    )

    # publish indicators.computed —— 让前端/UI 实时显示"指标流水线推进"
    if deps.outbox is not None:
        deps.outbox.record(
            db, aggregate_type="indicator_snapshot", aggregate_id=snap_id,
            event=IndicatorsComputed(
                symbol=symbol, timeframe=tf,
                open_time=latest_open_time,
                indicator_snapshot_id=snap_id,
            ),
            account_id=account_id, trading_mode=trading_mode,
            trace_id=trace_id,
        )

    factors, factor_snap_id = deps.factor_computer.compute_and_store(
        account_id=account_id, trading_mode=trading_mode,
        symbol=symbol, timeframe=tf,
        open_time=latest_open_time,
        indicators=values, candles_df=df,
    )

    if deps.outbox is not None:
        deps.outbox.record(
            db, aggregate_type="factor_snapshot", aggregate_id=factor_snap_id,
            event=FactorsUpdated(
                symbol=symbol, timeframe=tf,
                open_time=latest_open_time,
                factor_snapshot_id=factor_snap_id,
            ),
            account_id=account_id, trading_mode=trading_mode,
            trace_id=trace_id,
        )

    # 4. 分类 regime
    regime_result = deps.regime_classifier.classify_and_store(
        session=db,
        account_id=account_id, trading_mode=trading_mode,
        symbol=symbol, timeframe=tf,
        open_time=latest_open_time,
        factor_snapshot_id=factor_snap_id, factors=factors,
    )

    if deps.outbox is not None:
        # aggregate_id=None: RegimeClassifier 当前未暴露 regime_snapshot.id;
        # V0.1.1 RegimeSnapshot.factor_snapshot_id 列补齐后, 这里改为
        # 真实的 regime_snapshot_id (跟踪在 codereview I6/Minor 项)。
        deps.outbox.record(
            db, aggregate_type="regime_snapshot", aggregate_id=None,
            event=RegimeClassified(
                symbol=symbol, timeframe=tf,
                open_time=latest_open_time,
                regime=regime_result.regime,
                confidence=float(regime_result.confidence),
            ),
            account_id=account_id, trading_mode=trading_mode,
            trace_id=trace_id,
        )

    # 5. 当前价格
    ticker = deps.adapter.get_ticker(symbol)
    current_price = float(ticker.price)

    # 7. 当前持仓
    open_pos = db.execute(
        select(Position).where(
            Position.account_id == account_id,
            Position.trading_mode == trading_mode,
            Position.symbol == symbol,
            Position.status == PositionStatus.OPEN.value,
        )
    ).scalars().first()
    open_position_dict = None
    if open_pos:
        open_position_dict = {
            "quantity": float(open_pos.quantity),
            "entry_price": float(open_pos.entry_price),
            "stop_loss": float(open_pos.stop_loss),
            "take_profit": float(open_pos.take_profit) if open_pos.take_profit else None,
            "unrealized_pnl": float(open_pos.unrealized_pnl or 0),
        }

    indicators_dict = {
        "ema20": values.ema20, "ema50": values.ema50, "ema200": values.ema200,
        "rsi": values.rsi, "macd": values.macd,
        "macd_signal": values.macd_signal, "macd_hist": values.macd_hist,
        "atr": values.atr,
        "bb_upper": values.bb_upper, "bb_middle": values.bb_middle,
        "bb_lower": values.bb_lower,
        "volume_ma": values.volume_ma, "volatility": values.volatility,
    }

    pipeline_input = PipelineInput(
        account_id=account_id, trading_mode=trading_mode,
        symbol=symbol, timeframe=tf,
        current_price=current_price,
        indicators=indicators_dict,
        factors=factors,
        regime=regime_result.regime,
        open_position=open_position_dict,
        account_snapshot={
            "available_usdt": available_usdt,
            "daily_pnl": daily_pnl,
            "daily_pnl_pct": daily_pnl_pct,
        },
        factor_snapshot_id=factor_snap_id,
        atr=values.atr or 0.0,
    )

    # 8. 策略路由 → AI Trader (decision_id 直接来自 Solver, 无需反查)
    proposal, decision_id = deps.router.decide(pipeline_input)

    # publish decision.proposed —— Notifier / UI 实时拿决策摘要
    # 没走到 Solver (decision_id is None) 的场景不发, 因为没有 ai_decisions 行
    if deps.outbox is not None and decision_id is not None:
        deps.outbox.record(
            db, aggregate_type="ai_decision", aggregate_id=decision_id,
            event=DecisionProposed(
                decision_id=decision_id,
                symbol=symbol, timeframe=tf,
                action=proposal.action,
                confidence=float(proposal.confidence),
                source=proposal.source,
                strategy_mode=proposal.strategy_mode,
                is_fallback=proposal.is_fallback,
            ),
            account_id=account_id, trading_mode=trading_mode,
            trace_id=trace_id,
        )

    # 9. 执行守卫
    guard_dec = deps.guard.check(
        proposal=proposal, trading_mode=trading_mode,
        current_price=current_price, regime=regime_result.regime,
        available_usdt=available_usdt, daily_pnl=daily_pnl,
        daily_pnl_pct=daily_pnl_pct, atr=values.atr or 0.0,
    )

    # 10. 按 guard 结果路由
    action_taken = "SKIP"
    if guard_dec.result == "PASS":
        if proposal.action == "OPEN_LONG":
            # OPEN_LONG 由 LLM 主动产出, 必然走过 Solver, decision_id 必非 None
            deps.executor.open_long(
                proposal=proposal, decision_id=decision_id or 0,
                account_id=account_id, trading_mode=trading_mode,
                available_usdt=available_usdt,
                current_price=current_price,
            )
            action_taken = "OPEN_LONG"
        elif proposal.action == "CLOSE_LONG" and open_pos:
            deps.executor.close_long(
                position=open_pos, reason="ai_close",
                decision_id=decision_id,
                account_id=account_id, trading_mode=trading_mode,
            )
            action_taken = "CLOSE_LONG"

    return {
        "action": action_taken,
        "proposal_action": proposal.action,
        "guard": guard_dec.result,
        "regime": regime_result.regime,
        "is_fallback": proposal.is_fallback,
    }


def run_strategy_pipeline_once(
    *,
    db: Session,
    account_id: int,
    trading_mode: str,
    adapter: ExchangeAdapter,
    llm_client: LLMClient,
    risk_profile: RiskProfile,
    symbols: list[str],
    timeframes: list[str],
    outbox: Optional[OutboxWriter] = None,
) -> dict[str, dict]:
    """执行一次完整 pipeline; 返回 {symbol_tf: {action, guard, ...}}。"""
    summary: dict[str, dict] = {}

    # 服务层一次性装配, 给所有 symbol×tf 复用
    composer = PromptComposer(db)
    retriever = ExperienceRetriever(db)
    solver = DecisionSolver(db, llm_client)
    critic = ReviewCritic(db)
    ait = AITraderPipeline(
        db, composer=composer, retriever=retriever, solver=solver, critic=critic,
    )
    deps = _PipelineDeps(
        market=MarketDataService(db, adapter, outbox=outbox),
        indicator=IndicatorComputer(db),
        factor_computer=FactorComputer(db),
        regime_classifier=RegimeClassifier(),
        router=StrategyRouter(db, ai_trader=ait),
        guard=ExecutionGuard(db, risk_profile=risk_profile),
        executor=OrderExecutor(db, adapter, outbox=outbox),
        adapter=adapter,
        outbox=outbox,
    )

    # 0. 阻塞开新仓的两条腿统一查 KillSwitchService:
    #    a) 人工 pause (system_settings.kill_switch_state)
    #    b) 自动熔断 (今天未 resolved 的 CIRCUIT_BREAKER_TRIGGERED)
    if KillSwitchService(db).should_block_new_trades(
        account_id=account_id, trading_mode=trading_mode,
    ):
        logger.warning(
            "kill switch or circuit breaker active for account=%s; skipping pipeline",
            account_id,
        )
        for s in symbols:
            for tf in timeframes:
                summary[f"{s}:{tf}"] = {"action": "SKIP", "reason": "blocked_by_kill_switch"}
        return summary

    # 1+6. 同步账户快照 (整轮共享)
    account_svc = AccountStateService(db, adapter)
    snap = account_svc.sync_snapshot(account_id=account_id, trading_mode=trading_mode)
    available_usdt = float(snap.available_balance_usdt)
    daily_pnl = float(snap.daily_pnl)
    daily_pnl_pct = float(snap.daily_pnl_pct)

    for symbol in symbols:
        for tf in timeframes:
            key = f"{symbol}:{tf}"
            try:
                summary[key] = _run_one_symbol_tf(
                    db=db,
                    account_id=account_id, trading_mode=trading_mode,
                    symbol=symbol, tf=tf,
                    deps=deps,
                    available_usdt=available_usdt,
                    daily_pnl=daily_pnl,
                    daily_pnl_pct=daily_pnl_pct,
                )
                db.commit()
            except Exception:  # noqa: BLE001
                logger.exception("pipeline cycle failed for %s", key)
                summary[key] = {"action": "ERROR"}
                db.rollback()

    return summary
