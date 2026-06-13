"""Tests for AITraderPipeline — end-to-end orchestration with mock LLM."""
from __future__ import annotations

import json
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.llm.client import MockLLMClient
from src.models import AIDecision, Base, DecisionReview, PromptTemplate
from src.services.insight.experience.retriever import ExperienceRetriever
from src.services.strategy.decision_solver import DecisionSolver
from src.services.strategy.pipeline import AITraderPipeline, PipelineInput
from src.services.strategy.prompt_composer import PromptComposer
from src.services.strategy.review_critic import ReviewCritic


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        # Always seed an active prompt template so compose() succeeds.
        s.add(PromptTemplate(
            name="ait_default", version=1,
            system_template="sys ${symbol}",
            user_template="user ${current_price}",
            active=True,
        ))
        s.flush()
        yield s


def _pipeline(session, canned_response: str) -> AITraderPipeline:
    llm = MockLLMClient(canned_response=canned_response)
    return AITraderPipeline(
        session,
        composer=PromptComposer(session),
        retriever=ExperienceRetriever(session),
        solver=DecisionSolver(session, llm),
        critic=ReviewCritic(session),
    )


def _input() -> PipelineInput:
    return PipelineInput(
        account_id=1, trading_mode="testnet",
        symbol="BTCUSDT", timeframe="1h",
        current_price=50000.0,
        indicators={"ema20": 49000.0, "atr": 200.0, "rsi": 55.0},
        factors={"trend_strength": 0.7},
        regime="trending_up",
        open_position=None,
        account_snapshot={"available_usdt": 10_000.0, "daily_pnl": 0.0, "daily_pnl_pct": 0.0},
        factor_snapshot_id=42,
        atr=200.0,
        experience_limit=3,
    )


VALID_OPEN_LONG = json.dumps({
    "action": "OPEN_LONG",
    "confidence": 0.72,
    "entry_type": "MARKET",
    "entry_price": 50000.0,
    "stop_loss": 49800.0,  # SL distance = 200 = 1.0 ATR (in range)
    "take_profit": 50400.0,  # R/R = 2 (above threshold)
    "position_size_pct": 0.1,
    "strategy_mode": "ai_trend",
    "reasoning": ["uptrend intact"],
    "risk_note": "normal",
})


def test_happy_path_returns_open_long(session):
    pipeline = _pipeline(session, VALID_OPEN_LONG)
    proposal, decision_id = pipeline.run(_input())
    assert proposal.action == "OPEN_LONG"
    assert proposal.is_fallback is False
    # 走过 Solver 必有 decision_id
    assert decision_id is not None
    assert decision_id == session.query(AIDecision).one().id


def test_garbage_llm_returns_fallback_hold(session):
    pipeline = _pipeline(session, "not json")
    proposal, decision_id = pipeline.run(_input())
    assert proposal.action == "HOLD"
    assert proposal.is_fallback is True
    # Solver 阶段才回退, 仍然写了 ai_decisions 行
    assert decision_id is not None


def test_review_reject_returns_fallback_hold_with_parent(session):
    """Regime downtrend + OPEN_LONG → critic rejects → pipeline HOLDs."""
    pipeline = _pipeline(session, VALID_OPEN_LONG)
    inp = _input()
    inp.regime = "trending_down"  # forces critic reject
    proposal, decision_id = pipeline.run(inp)
    assert proposal.action == "HOLD"
    assert proposal.is_fallback is True
    # parent_proposal_id references the original ai_decisions row
    assert proposal.parent_proposal_id is not None
    assert decision_id == proposal.parent_proposal_id
    # Audit row count sanity
    reviews = session.query(DecisionReview).all()
    assert len(reviews) == 1
    assert reviews[0].result == "reject"


def test_review_adjust_patches_take_profit(session):
    """LLM's TP too close → critic adjusts → pipeline returns adjusted proposal."""
    tight_tp_response = json.dumps({
        "action": "OPEN_LONG", "confidence": 0.7,
        "entry_type": "MARKET", "entry_price": 50000.0,
        "stop_loss": 49800.0,   # SL distance = 200 (within 0.5–5 × ATR)
        "take_profit": 50200.0, # R/R = 1.0 < 1.5
        "position_size_pct": 0.1,
        "strategy_mode": "ai_trend",
        "reasoning": ["too close"],
    })
    pipeline = _pipeline(session, tight_tp_response)
    proposal, decision_id = pipeline.run(_input())
    assert proposal.action == "OPEN_LONG"
    assert proposal.is_fallback is False
    # Adjustment bumped TP to entry + 200 * 1.5 = 50300
    assert abs(proposal.take_profit - 50300.0) < 0.01
    assert "review_adjust" in (proposal.risk_note or "")
    assert decision_id is not None
    # parent_proposal_id 指回 Solver 的 ai_decisions.id
    assert proposal.parent_proposal_id == decision_id


def test_missing_prompt_template_returns_fallback(session):
    """If prompt_templates is empty, pipeline falls back (no uncaught raise)."""
    session.query(PromptTemplate).delete()
    session.flush()
    pipeline = _pipeline(session, VALID_OPEN_LONG)
    proposal, decision_id = pipeline.run(_input())
    assert proposal.is_fallback is True
    assert "prompt_template_missing" in proposal.reasoning[0]
    # 提前回退 → 没有 ai_decisions 行
    assert decision_id is None


def test_full_run_persists_audit_trail(session):
    """Happy path: 1 proposal_drafts + 1 ai_decisions + 1 decision_reviews rows."""
    pipeline = _pipeline(session, VALID_OPEN_LONG)
    pipeline.run(_input())
    from src.models import ProposalDraft
    assert session.query(ProposalDraft).count() == 1
    assert session.query(AIDecision).count() == 1
    assert session.query(DecisionReview).count() == 1


def test_proposal_draft_carries_trading_mode(session):
    """PromptContext.trading_mode 应写入 ProposalDraft, 不再硬编码 testnet."""
    from src.models import ProposalDraft

    pipeline = _pipeline(session, VALID_OPEN_LONG)
    inp = _input()
    inp.trading_mode = "mainnet"
    pipeline.run(inp)

    draft = session.query(ProposalDraft).one()
    assert draft.trading_mode == "mainnet"
