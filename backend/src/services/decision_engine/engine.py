"""AI 决策引擎 — 调用 LLM 生成结构化交易决策并写入 DB。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from src.services.decision_engine.parser import DecisionPayload, parse_llm_output
from src.services.decision_engine.prompt import (
    SYSTEM_PROMPT,
    build_prompt_input,
    format_user_message,
)
from src.shared.config import get_settings
from src.shared.config_diagnostics import can_call_llm, get_runtime_credential_status
from src.models.decision import AIDecision

logger = logging.getLogger(__name__)


def _call_llm(system: str, user: str) -> str:
    """调用 LLM (OpenAI 兼容协议)，返回原始文本输出。超时或失败返回空字符串。"""
    settings = get_settings()
    if not can_call_llm(settings):
        diag = get_runtime_credential_status(settings)["llm"]
        logger.warning("Skipping LLM call because runtime LLM config is not usable: %s", diag["reason"])
        return ""

    try:
        import openai
        client_kwargs: dict[str, object] = {"api_key": settings.LLM_API_KEY}
        if settings.LLM_BASE_URL:
            client_kwargs["base_url"] = settings.LLM_BASE_URL
        client = openai.OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=1024,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        return ""


def make_decision(
    db: Session,
    symbol: str,
    timeframe: str,
    current_price: float,
    indicators: dict[str, Any],
    regime: dict[str, Any],
    account: dict[str, Any],
    open_position: dict[str, Any] | None = None,
    recent_experience: list[dict[str, Any]] | None = None,
) -> tuple[DecisionPayload, AIDecision]:
    """
    调用 LLM 生成决策，解析输出，写入 ai_decisions 表，返回 (payload, db_record)。
    任何失败都回退到 HOLD。
    """
    settings = get_settings()

    prompt_input = build_prompt_input(
        symbol=symbol,
        timeframe=timeframe,
        current_price=current_price,
        indicators=indicators,
        regime=regime,
        account=account,
        open_position=open_position,
        recent_experience=recent_experience,
    )
    user_message = format_user_message(prompt_input)

    logger.info("Calling LLM for decision: %s %s price=%.4f", symbol, timeframe, current_price)
    raw_output = _call_llm(SYSTEM_PROMPT, user_message)

    payload = parse_llm_output(raw_output, symbol, timeframe)

    record = AIDecision(
        trading_mode=settings.TRADING_MODE.value,
        symbol=payload.symbol,
        timeframe=payload.timeframe,
        decided_at=datetime.now(tz=timezone.utc),
        action=payload.action.value,
        confidence=payload.confidence,
        entry_type=payload.entry_type.value if payload.entry_type else None,
        entry_price=payload.entry_price,
        stop_loss=payload.stop_loss,
        take_profit=payload.take_profit,
        position_size_pct=payload.position_size_pct,
        strategy_mode=payload.strategy_mode.value if payload.strategy_mode else None,
        reasoning=payload.reasoning,
        risk_note=payload.risk_note,
        prompt_input=prompt_input,
        raw_output=raw_output,
        is_fallback=payload.is_fallback,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info(
        "Decision stored id=%d: action=%s confidence=%.2f is_fallback=%s",
        record.id,
        payload.action.value,
        payload.confidence,
        payload.is_fallback,
    )
    return payload, record
