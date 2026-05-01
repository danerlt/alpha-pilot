"""Tests for DecisionProposal pydantic contract."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.services.strategy.proposal import DecisionProposal


def test_open_long_proposal_constructs():
    p = DecisionProposal(
        account_id=1, symbol="BTCUSDT", timeframe="1h",
        action="OPEN_LONG", confidence=0.72,
        entry_type="MARKET", entry_price=50000.0,
        stop_loss=49000.0, take_profit=52000.0,
        position_size_pct=0.1,
        strategy_mode="ai_trend",
        source="ai_trader",
    )
    assert p.action == "OPEN_LONG"
    assert p.is_fallback is False
    assert p.pipeline_version == "v0.1"
    assert p.reasoning == []


def test_confidence_out_of_range_rejected():
    with pytest.raises(ValidationError):
        DecisionProposal(
            account_id=1, symbol="X", timeframe="1h",
            action="HOLD", confidence=1.5,
            strategy_mode="ai_observation", source="ai_trader",
        )
    with pytest.raises(ValidationError):
        DecisionProposal(
            account_id=1, symbol="X", timeframe="1h",
            action="HOLD", confidence=-0.1,
            strategy_mode="ai_observation", source="ai_trader",
        )


def test_action_open_short_rejected():
    with pytest.raises(ValidationError):
        DecisionProposal(
            account_id=1, symbol="X", timeframe="1h",
            action="OPEN_SHORT",  # not in V0.1 Literal
            confidence=0.5,
            strategy_mode="ai_trend", source="ai_trader",
        )


def test_strategy_mode_restricted_to_whitelist():
    with pytest.raises(ValidationError):
        DecisionProposal(
            account_id=1, symbol="X", timeframe="1h",
            action="HOLD", confidence=0.0,
            strategy_mode="random_guess",  # not a whitelisted mode
            source="ai_trader",
        )


def test_source_restricted_to_four_values():
    with pytest.raises(ValidationError):
        DecisionProposal(
            account_id=1, symbol="X", timeframe="1h",
            action="HOLD", confidence=0.0,
            strategy_mode="ai_observation",
            source="external",  # not one of ai_trader/program_trader/shadow/manual
        )


def test_position_size_pct_bounds():
    # Upper bound (1.0) allowed.
    DecisionProposal(
        account_id=1, symbol="X", timeframe="1h",
        action="HOLD", confidence=0.0,
        position_size_pct=1.0,
        strategy_mode="ai_observation", source="ai_trader",
    )
    # Over bound rejected.
    with pytest.raises(ValidationError):
        DecisionProposal(
            account_id=1, symbol="X", timeframe="1h",
            action="HOLD", confidence=0.0,
            position_size_pct=1.1,
            strategy_mode="ai_observation", source="ai_trader",
        )


# post-Plan5 安全审计 C6: NaN / Inf / 负数价格必须被 Pydantic 拒
class TestRejectsNonFiniteAndNegative:
    def test_nan_stop_loss_rejected(self):
        with pytest.raises(ValidationError):
            DecisionProposal(
                account_id=1, symbol="X", timeframe="1h",
                action="OPEN_LONG", confidence=0.5,
                entry_type="MARKET", entry_price=50000.0,
                stop_loss=float("nan"), take_profit=51000.0,
                position_size_pct=0.1,
                strategy_mode="ai_trend", source="ai_trader",
            )

    def test_inf_take_profit_rejected(self):
        with pytest.raises(ValidationError):
            DecisionProposal(
                account_id=1, symbol="X", timeframe="1h",
                action="OPEN_LONG", confidence=0.5,
                entry_type="MARKET", entry_price=50000.0,
                stop_loss=49000.0, take_profit=float("inf"),
                position_size_pct=0.1,
                strategy_mode="ai_trend", source="ai_trader",
            )

    def test_negative_entry_price_rejected(self):
        with pytest.raises(ValidationError):
            DecisionProposal(
                account_id=1, symbol="X", timeframe="1h",
                action="OPEN_LONG", confidence=0.5,
                entry_type="MARKET", entry_price=-50000.0,
                stop_loss=49000.0, take_profit=51000.0,
                position_size_pct=0.1,
                strategy_mode="ai_trend", source="ai_trader",
            )

    def test_zero_stop_loss_rejected(self):
        with pytest.raises(ValidationError):
            DecisionProposal(
                account_id=1, symbol="X", timeframe="1h",
                action="OPEN_LONG", confidence=0.5,
                entry_type="MARKET", entry_price=50000.0,
                stop_loss=0.0, take_profit=51000.0,
                position_size_pct=0.1,
                strategy_mode="ai_trend", source="ai_trader",
            )

    def test_nan_position_size_rejected(self):
        with pytest.raises(ValidationError):
            DecisionProposal(
                account_id=1, symbol="X", timeframe="1h",
                action="HOLD", confidence=0.0,
                position_size_pct=float("nan"),
                strategy_mode="ai_observation", source="ai_trader",
            )

    def test_nan_confidence_rejected(self):
        with pytest.raises(ValidationError):
            DecisionProposal(
                account_id=1, symbol="X", timeframe="1h",
                action="HOLD", confidence=float("nan"),
                strategy_mode="ai_observation", source="ai_trader",
            )


def test_decision_solver_rejects_nan_in_llm_json():
    """post-Plan5 安全审计 C6: LLM 输出 {"stop_loss": NaN} 必须在 json.loads
    阶段就被拒, 不能让 NaN 进 Pydantic."""
    from src.services.strategy.decision_solver import _parse_llm_json

    with pytest.raises(ValueError, match="non-finite"):
        _parse_llm_json('{"action":"OPEN_LONG","stop_loss":NaN,"position_size_pct":0.1}')


def test_decision_solver_rejects_infinity():
    from src.services.strategy.decision_solver import _parse_llm_json

    with pytest.raises(ValueError, match="non-finite"):
        _parse_llm_json('{"take_profit": Infinity}')


def test_fallback_hold_factory():
    p = DecisionProposal.fallback_hold(
        account_id=1, symbol="BTCUSDT", timeframe="1h",
        reason="llm_timeout",
    )
    assert p.action == "HOLD"
    assert p.is_fallback is True
    assert p.confidence == 0.0
    assert p.strategy_mode == "ai_observation"
    assert p.source == "ai_trader"
    assert "llm_timeout" in p.reasoning[0]


def test_fallback_hold_preserves_parent_and_factor_ids():
    p = DecisionProposal.fallback_hold(
        account_id=1, symbol="BTCUSDT", timeframe="1h",
        reason="review_reject",
        parent_proposal_id=42,
        factor_snapshot_id=99,
    )
    assert p.parent_proposal_id == 42
    assert p.factor_snapshot_id == 99
