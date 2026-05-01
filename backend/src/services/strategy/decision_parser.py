"""LLM 输出解析 — JSON 解析 + 兜底 HOLD。"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from src.common.enums import Action, EntryType, StrategyMode

logger = logging.getLogger(__name__)

VALID_ACTIONS = {a.value for a in Action}
VALID_ENTRY_TYPES = {e.value for e in EntryType}
VALID_STRATEGY_MODES = {s.value for s in StrategyMode}


@dataclass
class DecisionPayload:
    symbol: str
    timeframe: str
    action: Action
    confidence: float = 0.5
    entry_type: EntryType | None = None
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    position_size_pct: float | None = None
    strategy_mode: StrategyMode | None = None
    reasoning: list[str] = field(default_factory=list)
    risk_note: str | None = None
    is_fallback: bool = False

    @staticmethod
    def hold_fallback(symbol: str, timeframe: str, reason: str = "parse_error") -> "DecisionPayload":
        return DecisionPayload(
            symbol=symbol,
            timeframe=timeframe,
            action=Action.HOLD,
            confidence=0.0,
            reasoning=[f"Fallback HOLD: {reason}"],
            is_fallback=True,
        )


def _extract_json(text: str) -> str:
    """从 LLM 输出中提取 JSON 块（处理 markdown code fences）。"""
    # 尝试提取 ```json ... ``` 块
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    # 直接找第一个 { ... }
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def parse_llm_output(
    raw_output: str,
    symbol: str,
    timeframe: str,
) -> DecisionPayload:
    """解析 LLM 输出，失败时返回 HOLD 兜底。"""
    if not raw_output or not raw_output.strip():
        logger.warning("Empty LLM output for %s %s", symbol, timeframe)
        return DecisionPayload.hold_fallback(symbol, timeframe, "empty_output")

    try:
        json_str = _extract_json(raw_output)
        data: dict[str, Any] = json.loads(json_str)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("JSON parse failed for %s %s: %s", symbol, timeframe, e)
        return DecisionPayload.hold_fallback(symbol, timeframe, f"json_parse_error:{e}")

    # 验证 action
    action_str = str(data.get("action", "")).upper()
    if action_str not in VALID_ACTIONS:
        logger.warning("Invalid action '%s' for %s %s", action_str, symbol, timeframe)
        return DecisionPayload.hold_fallback(symbol, timeframe, f"invalid_action:{action_str}")

    action = Action(action_str)

    # OPEN_LONG 必须有 stop_loss
    if action == Action.OPEN_LONG:
        if not data.get("stop_loss"):
            logger.warning("OPEN_LONG without stop_loss for %s %s", symbol, timeframe)
            return DecisionPayload.hold_fallback(symbol, timeframe, "missing_stop_loss")
        entry_price = data.get("entry_price")
        stop_loss = float(data["stop_loss"])
        if entry_price and float(entry_price) <= stop_loss:
            logger.warning("stop_loss >= entry_price for %s %s", symbol, timeframe)
            return DecisionPayload.hold_fallback(symbol, timeframe, "invalid_stop_loss")

    # entry_type
    entry_type_str = str(data.get("entry_type", "")).upper()
    entry_type = EntryType(entry_type_str) if entry_type_str in VALID_ENTRY_TYPES else None

    # strategy_mode
    sm_str = str(data.get("strategy_mode", "")).lower()
    strategy_mode = StrategyMode(sm_str) if sm_str in VALID_STRATEGY_MODES else None

    # position_size_pct 边界
    pos_size = data.get("position_size_pct")
    if pos_size is not None:
        pos_size = max(0.01, min(0.20, float(pos_size)))

    # confidence 边界
    confidence = float(data.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))

    reasoning = data.get("reasoning", [])
    if isinstance(reasoning, str):
        reasoning = [reasoning]

    return DecisionPayload(
        symbol=data.get("symbol", symbol),
        timeframe=data.get("timeframe", timeframe),
        action=action,
        confidence=confidence,
        entry_type=entry_type,
        entry_price=float(data["entry_price"]) if data.get("entry_price") else None,
        stop_loss=float(data["stop_loss"]) if data.get("stop_loss") else None,
        take_profit=float(data["take_profit"]) if data.get("take_profit") else None,
        position_size_pct=pos_size,
        strategy_mode=strategy_mode,
        reasoning=reasoning,
        risk_note=data.get("risk_note"),
        is_fallback=False,
    )
