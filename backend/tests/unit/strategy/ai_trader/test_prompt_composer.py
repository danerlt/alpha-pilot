"""Tests for PromptComposer."""
from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.strategy.ai_trader.prompt_composer import (
    PromptComposer,
    PromptContext,
    PromptTemplateNotFound,
)
from src.models import Base, ProposalDraft, PromptTemplate


@pytest.fixture
def session():
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", os.environ.get("TEST_DATABASE_URL", os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))))
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _seed_active_template(session, *, name="ait_default"):
    tpl = PromptTemplate(
        name=name,
        version=1,
        system_template="You trade ${symbol} on ${timeframe}. Regime=${regime}.",
        user_template="Price=${current_price} indicators=${indicators_json} factors=${factors_json}",
        active=True,
    )
    session.add(tpl)
    session.flush()
    return tpl


def _sample_context(symbol="BTCUSDT", trading_mode="testnet") -> PromptContext:
    return PromptContext(
        account_id=1, trading_mode=trading_mode, symbol=symbol, timeframe="1h",
        current_price=50_000.0,
        indicators={"ema20": 49_000.0, "rsi": 55.0, "atr": 250.0},
        factors={"trend_strength": 0.7, "volume_confirmation": 0.3},
        regime="trending_up",
        open_position=None,
        account_snapshot={"available_usdt": 10_000.0, "daily_pnl": 0.0, "daily_pnl_pct": 0.0},
        recent_experience=[],
    )


def test_compose_renders_template_and_persists_draft(session):
    _seed_active_template(session)
    composer = PromptComposer(session)

    bundle = composer.compose(_sample_context())
    assert "BTCUSDT" in bundle.system
    assert "trending_up" in bundle.system
    assert "50000" in bundle.user
    assert "trend_strength" in bundle.user
    assert len(bundle.context_hash) == 64  # SHA-256 hex

    row = session.get(ProposalDraft, bundle.proposal_draft_id)
    assert row is not None
    assert row.symbol == "BTCUSDT"
    assert row.context_hash == bundle.context_hash


def test_compose_raises_when_no_active_template(session):
    composer = PromptComposer(session)
    with pytest.raises(PromptTemplateNotFound):
        composer.compose(_sample_context())


def test_compose_picks_highest_version_active_template(session):
    session.add(PromptTemplate(
        name="ait_default", version=1, system_template="v1", user_template="v1",
        active=True,
    ))
    session.add(PromptTemplate(
        name="ait_default", version=3, system_template="v3", user_template="v3",
        active=True,
    ))
    session.add(PromptTemplate(
        name="ait_default", version=2, system_template="v2", user_template="v2",
        active=True,
    ))
    session.flush()

    bundle = PromptComposer(session).compose(_sample_context())
    # Highest active version wins (v3).
    assert bundle.template_version == 3


def test_compose_ignores_inactive_templates(session):
    session.add(PromptTemplate(
        name="ait_default", version=1,
        system_template="v1", user_template="v1",
        active=False,
    ))
    session.flush()
    with pytest.raises(PromptTemplateNotFound):
        PromptComposer(session).compose(_sample_context())


def test_context_hash_is_deterministic(session):
    _seed_active_template(session)
    composer = PromptComposer(session)
    b1 = composer.compose(_sample_context())
    b2 = composer.compose(_sample_context())
    # Same input → same hash.
    assert b1.context_hash == b2.context_hash
    # Two rows written though (each compose call is its own audit record).
    rows = session.execute(select(ProposalDraft)).scalars().all()
    assert len(rows) == 2


def test_different_context_produces_different_hash(session):
    _seed_active_template(session)
    composer = PromptComposer(session)
    a = composer.compose(_sample_context(symbol="BTCUSDT"))
    b = composer.compose(_sample_context(symbol="ETHUSDT"))
    assert a.context_hash != b.context_hash


def test_compose_writes_trading_mode_from_context(session):
    """ProposalDraft.trading_mode 应来自 PromptContext, 不再硬编码 testnet."""
    _seed_active_template(session)
    composer = PromptComposer(session)
    bundle = composer.compose(_sample_context(trading_mode="mainnet"))
    row = session.get(ProposalDraft, bundle.proposal_draft_id)
    assert row.trading_mode == "mainnet"


def test_different_trading_mode_yields_different_hash(session):
    """testnet / mainnet 的 context_hash 必须不同, 否则两环境会被错误去重."""
    _seed_active_template(session)
    composer = PromptComposer(session)
    a = composer.compose(_sample_context(trading_mode="testnet"))
    b = composer.compose(_sample_context(trading_mode="mainnet"))
    assert a.context_hash != b.context_hash


def test_compose_survives_empty_recent_experience_and_no_position(session):
    """Common case: cold start, no position, no past trades — must not raise."""
    session.add(PromptTemplate(
        name="ait_default", version=1,
        system_template="sys ${symbol}",
        # Reference the two fields so the template actually renders them.
        user_template="pos=${open_position_json} exp=${recent_experience_json}",
        active=True,
    ))
    session.flush()
    composer = PromptComposer(session)
    bundle = composer.compose(_sample_context())
    # None → "null"; [] → "[]".
    assert "null" in bundle.user
    assert "[]" in bundle.user
