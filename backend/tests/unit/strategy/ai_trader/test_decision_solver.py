"""Tests for DecisionSolver — parse + validate + persist + fallback HOLD."""
from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.models import AIDecision, Base
from src.strategy.ai_trader.decision_solver import DecisionSolver
from src.strategy.ai_trader.llm_client import MockLLMClient
from src.strategy.ai_trader.prompt_composer import PromptBundle


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _bundle() -> PromptBundle:
    """Fixed bundle for DecisionSolver tests — no real template rendering."""
    return PromptBundle(
        proposal_draft_id=1,
        template_id=10,
        template_name="ait_default",
        template_version=1,
        system="sys",
        user="user",
        context_hash="h" * 64,
    )


def _solve(session, canned: str):
    llm = MockLLMClient(canned_response=canned)
    solver = DecisionSolver(session, llm)
    return solver.solve(
        prompt_bundle=_bundle(),
        account_id=1,
        trading_mode="testnet",
        symbol="BTCUSDT",
        timeframe="1h",
        factor_snapshot_id=42,
    )


VALID_OPEN_LONG = json.dumps({
    "action": "OPEN_LONG",
    "confidence": 0.72,
    "entry_type": "MARKET",
    "entry_price": 50000.0,
    "stop_loss": 49000.0,
    "take_profit": 52000.0,
    "position_size_pct": 0.1,
    "strategy_mode": "ai_trend",
    "reasoning": ["EMA stack bullish", "volume rising"],
    "risk_note": "tight SL",
})


def test_valid_open_long_parses_and_persists(session):
    proposal, decision_id = _solve(session, VALID_OPEN_LONG)
    assert proposal.action == "OPEN_LONG"
    assert proposal.is_fallback is False
    assert proposal.confidence == 0.72
    assert proposal.stop_loss == 49000.0

    row = session.get(AIDecision, decision_id)
    assert row.action == "OPEN_LONG"
    assert row.is_fallback is False
    assert row.proposal_draft_id == 1
    assert row.factor_snapshot_id == 42


def test_code_fenced_json_is_handled(session):
    fenced = "Sure! Here's the decision:\n```json\n" + VALID_OPEN_LONG + "\n```"
    proposal, _ = _solve(session, fenced)
    assert proposal.action == "OPEN_LONG"
    assert proposal.is_fallback is False


def test_invalid_json_falls_back_to_hold(session):
    proposal, decision_id = _solve(session, "oh hi mark")
    assert proposal.action == "HOLD"
    assert proposal.is_fallback is True
    row = session.get(AIDecision, decision_id)
    assert row.is_fallback is True
    assert row.raw_output == "oh hi mark"  # preserved for audit


def test_open_short_action_falls_back(session):
    """V0.1 rejects OPEN_SHORT — long-only."""
    bad = json.dumps({"action": "OPEN_SHORT", "confidence": 0.5, "strategy_mode": "ai_trend"})
    proposal, _ = _solve(session, bad)
    assert proposal.action == "HOLD"
    assert proposal.is_fallback is True


def test_missing_stop_loss_falls_back_when_action_is_open_long(session):
    bad = json.dumps({
        "action": "OPEN_LONG", "confidence": 0.7,
        "entry_type": "MARKET", "entry_price": 50000.0,
        "stop_loss": None, "take_profit": 52000.0,
        "position_size_pct": 0.1, "strategy_mode": "ai_trend",
    })
    proposal, _ = _solve(session, bad)
    assert proposal.is_fallback is True
    assert proposal.action == "HOLD"


def test_hard_cap_violation_falls_back(session):
    """Per spec §1.4, position_size_pct > 0.20 is a hard cap — unparsable."""
    bad_data = json.loads(VALID_OPEN_LONG)
    bad_data["position_size_pct"] = 0.5  # way over cap
    proposal, _ = _solve(session, json.dumps(bad_data))
    assert proposal.is_fallback is True


def test_llm_timeout_falls_back_without_raising(session):
    """Pipeline cycle is 15 min; skip trade rather than retry on the hot path."""
    llm = MockLLMClient(canned_response=VALID_OPEN_LONG, raise_timeout_after=0)  # 1st call raises
    solver = DecisionSolver(session, llm)
    proposal, _ = solver.solve(
        prompt_bundle=_bundle(), account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h", factor_snapshot_id=None,
    )
    assert proposal.is_fallback is True
    assert proposal.action == "HOLD"
    assert "llm_timeout" in proposal.reasoning[0]


def test_fallback_decision_row_still_persists_prompt_and_factor_refs(session):
    """Even on fallback we want the audit trail — draft id + factor snapshot id."""
    proposal, decision_id = _solve(session, "garbage")
    row = session.get(AIDecision, decision_id)
    assert row.is_fallback is True
    assert row.proposal_draft_id == 1
    assert row.factor_snapshot_id == 42
    assert row.llm_provider == "mock"  # llm was called even though parsing failed


def test_valid_hold_passes_without_stop_loss(session):
    """HOLD is allowed to have no stop_loss — it's not a trade."""
    good = json.dumps({
        "action": "HOLD", "confidence": 0.3,
        "strategy_mode": "ai_observation",
        "reasoning": ["no edge"],
    })
    proposal, _ = _solve(session, good)
    assert proposal.action == "HOLD"
    assert proposal.is_fallback is False
