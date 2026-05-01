"""APScheduler 任务包装层 (Plan 5)。

把 Plan 2 的 run_strategy_pipeline_once / run_position_monitor_once 封装成
APScheduler 可调用的零参函数, 自带依赖注入 + KillSwitch 检查 + 错误兜底。

app.py lifespan + scheduler 进程统一用这里的 V1 jobs 触发完整决策链。
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.controllers.dependencies import get_adapter
from src.services.risk.kill_switch import KillSwitchService
from src.services.events.outbox import OutboxWriter
from src.core.exchange.binance_adapter import BinanceAdapter
from src.configs.app_configs import get_settings
from src.db.engines import get_session_factory
from src.models.account_entity import RiskProfile
from src.core.llm.client import (
    LLMClient,
    MockLLMClient,
    OpenAIClient,
)
from src.workers.position_monitor_worker import run_position_monitor_once
from src.workers.strategy_pipeline import run_strategy_pipeline_once

logger = logging.getLogger(__name__)


def _build_adapter(settings=None) -> BinanceAdapter:
    """构造 BinanceAdapter — 兼容老调用 (有 settings 入参) 但实际转发到统一的
    src.controllers.dependencies.get_adapter, 让 commands router / scheduler_jobs 共用一处.

    settings 入参当前忽略 (从 get_settings 重新取), 主要保留是为了不破现有
    monkeypatch 测试. 后续 V0.1.1 完整切到 get_adapter 后可删.
    """
    return get_adapter()


def _build_llm(settings) -> LLMClient:
    """统一走 OpenAI 兼容客户端; 占位 key 时回退 MockLLMClient (永远 HOLD)."""
    api_key = settings.LLM_API_KEY
    if not api_key or api_key.startswith("test-"):
        logger.warning("LLM_API_KEY is placeholder; using MockLLMClient (HOLD only)")
        return MockLLMClient(canned_response='{"action":"HOLD","confidence":0.0,"strategy_mode":"ai_observation","reasoning":["llm_disabled"]}')
    return OpenAIClient(
        api_key=api_key,
        model=settings.LLM_MODEL,
        base_url=settings.LLM_BASE_URL,
    )


def _load_active_risk_profile(session: Session, account_id: int) -> Optional[RiskProfile]:
    return session.execute(
        select(RiskProfile).where(
            RiskProfile.account_id == account_id,
            RiskProfile.active.is_(True),
        ).order_by(RiskProfile.version.desc()).limit(1)
    ).scalars().first()


def _parse_csv(value: str) -> list[str]:
    return [s.strip() for s in value.split(",") if s.strip()]


def new_strategy_pipeline_job() -> None:
    """APScheduler 每 STRATEGY_LOOP_INTERVAL_MINUTES 调一次.

    早期 short-circuit: 人工 pause 立刻退出, 不浪费连接 / 不构造 adapter.
    熔断 (RiskEvent) 由 strategy_pipeline 内部 KillSwitchService.should_block_new_trades
    再次检查, 这里只 cover 人工 pause 这一最常见的 ops 场景。
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        if KillSwitchService(db).is_paused():
            logger.info("kill_switch=paused; new strategy pipeline skipped")
            return
        settings = get_settings()
        profile = _load_active_risk_profile(db, account_id=1)
        if profile is None:
            logger.warning("no active risk_profile for account_id=1; pipeline skipped")
            return
        adapter = _build_adapter(settings)
        llm = _build_llm(settings)
        outbox = OutboxWriter()
        symbols = _parse_csv(settings.PIPELINE_SYMBOLS)
        timeframes = _parse_csv(settings.PIPELINE_TIMEFRAMES)
        summary = run_strategy_pipeline_once(
            db=db, account_id=1,
            trading_mode=settings.TRADING_MODE.value,
            adapter=adapter, llm_client=llm,
            risk_profile=profile,
            symbols=symbols, timeframes=timeframes,
            outbox=outbox,
        )
        logger.info("strategy_pipeline summary: %s", summary)
    except Exception:
        logger.exception("new_strategy_pipeline_job error")
    finally:
        db.close()


def new_position_monitor_job() -> None:
    """APScheduler 每 POSITION_MONITOR_INTERVAL_SECONDS 调一次.

    设计决策 (Plan 5 codereview I2): position_monitor 不接 KillSwitch.
    SL/TP 必须无条件运行保护已开仓位 — 人工 pause / 自动熔断都只阻止
    strategy_pipeline 开"新"仓, 现存仓位的风控必须持续跑直到平仓。
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        settings = get_settings()
        adapter = _build_adapter(settings)
        outbox = OutboxWriter()
        result = run_position_monitor_once(
            db=db, account_id=1,
            trading_mode=settings.TRADING_MODE.value,
            adapter=adapter,
            max_daily_loss_pct=settings.MAX_DAILY_LOSS_PCT,
            outbox=outbox,
        )
        if result.stop_loss_closed or result.take_profit_closed or result.circuit_breaker_triggered:
            logger.info(
                "position_monitor: SL=%s TP=%s breaker=%s",
                result.stop_loss_closed, result.take_profit_closed,
                result.circuit_breaker_triggered,
            )
    except Exception:
        logger.exception("new_position_monitor_job error")
    finally:
        db.close()
