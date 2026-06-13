"""单元测试：LLM 输出解析器 (decision_engine/parser.py)。"""
import json

import pytest

from src.common.enums import Action
from src.services.strategy.decision_parser import DecisionPayload, parse_llm_output

# ─── 兜底（Fallback）场景 ──────────────────────────────────────────────────────

def test_empty_output_returns_hold_fallback():
    result = parse_llm_output("", "BTCUSDT", "15m")
    assert result.action == Action.HOLD
    assert result.is_fallback is True


def test_whitespace_only_returns_hold_fallback():
    result = parse_llm_output("   \n\t  ", "BTCUSDT", "15m")
    assert result.action == Action.HOLD
    assert result.is_fallback is True


def test_invalid_json_returns_hold_fallback():
    result = parse_llm_output("not json at all }{", "BTCUSDT", "15m")
    assert result.action == Action.HOLD
    assert result.is_fallback is True


def test_invalid_action_returns_hold_fallback():
    payload = json.dumps({"action": "SHORT", "symbol": "BTCUSDT"})
    result = parse_llm_output(payload, "BTCUSDT", "15m")
    assert result.action == Action.HOLD
    assert result.is_fallback is True


def test_open_long_missing_stop_loss_returns_fallback():
    payload = json.dumps({
        "action": "OPEN_LONG",
        "symbol": "BTCUSDT",
        "entry_price": 50000,
        "confidence": 0.8,
    })
    result = parse_llm_output(payload, "BTCUSDT", "15m")
    assert result.action == Action.HOLD
    assert result.is_fallback is True


def test_open_long_stop_loss_above_entry_returns_fallback():
    payload = json.dumps({
        "action": "OPEN_LONG",
        "symbol": "BTCUSDT",
        "entry_price": 50000,
        "stop_loss": 51000,  # stop_loss > entry_price — invalid
        "confidence": 0.8,
    })
    result = parse_llm_output(payload, "BTCUSDT", "15m")
    assert result.action == Action.HOLD
    assert result.is_fallback is True


def test_json_in_markdown_code_fence():
    payload = '```json\n{"action": "HOLD", "symbol": "BTCUSDT", "confidence": 0.5}\n```'
    result = parse_llm_output(payload, "BTCUSDT", "15m")
    assert result.action == Action.HOLD
    assert result.is_fallback is False


# ─── 正常解析 ─────────────────────────────────────────────────────────────────

def test_valid_hold():
    payload = json.dumps({
        "action": "HOLD",
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "confidence": 0.6,
        "reasoning": ["Market is choppy"],
    })
    result = parse_llm_output(payload, "BTCUSDT", "15m")
    assert result.action == Action.HOLD
    assert result.confidence == pytest.approx(0.6)
    assert result.is_fallback is False
    assert result.symbol == "BTCUSDT"


def test_valid_open_long():
    payload = json.dumps({
        "action": "OPEN_LONG",
        "symbol": "ETHUSDT",
        "timeframe": "1h",
        "entry_price": 3000.0,
        "stop_loss": 2900.0,
        "take_profit": 3200.0,
        "position_size_pct": 0.10,
        "confidence": 0.75,
        "reasoning": ["EMA trending up", "RSI not overbought"],
        "risk_note": "Tight stop below support",
    })
    result = parse_llm_output(payload, "ETHUSDT", "1h")
    assert result.action == Action.OPEN_LONG
    assert result.stop_loss == pytest.approx(2900.0)
    assert result.entry_price == pytest.approx(3000.0)
    assert result.take_profit == pytest.approx(3200.0)
    assert result.position_size_pct == pytest.approx(0.10)
    assert result.is_fallback is False


def test_valid_close_long():
    payload = json.dumps({
        "action": "CLOSE_LONG",
        "symbol": "BTCUSDT",
        "confidence": 0.9,
    })
    result = parse_llm_output(payload, "BTCUSDT", "15m")
    assert result.action == Action.CLOSE_LONG
    assert result.is_fallback is False


def test_confidence_clamped_to_range():
    payload = json.dumps({"action": "HOLD", "confidence": 5.0})
    result = parse_llm_output(payload, "BTCUSDT", "15m")
    assert result.confidence == pytest.approx(1.0)

    payload2 = json.dumps({"action": "HOLD", "confidence": -1.0})
    result2 = parse_llm_output(payload2, "BTCUSDT", "15m")
    assert result2.confidence == pytest.approx(0.0)


def test_position_size_clamped_to_range():
    payload = json.dumps({
        "action": "OPEN_LONG",
        "entry_price": 100.0,
        "stop_loss": 90.0,
        "position_size_pct": 0.99,  # exceeds max, should be clamped to 0.20
    })
    result = parse_llm_output(payload, "BTCUSDT", "15m")
    assert result.position_size_pct == pytest.approx(0.20)


def test_reasoning_string_converted_to_list():
    payload = json.dumps({"action": "HOLD", "reasoning": "Just a string"})
    result = parse_llm_output(payload, "BTCUSDT", "15m")
    assert isinstance(result.reasoning, list)
    assert result.reasoning == ["Just a string"]


def test_hold_fallback_factory():
    fb = DecisionPayload.hold_fallback("BTCUSDT", "15m", "test_reason")
    assert fb.action == Action.HOLD
    assert fb.is_fallback is True
    assert fb.confidence == 0.0
    assert "test_reason" in fb.reasoning[0]
