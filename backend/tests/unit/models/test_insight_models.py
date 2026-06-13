from __future__ import annotations

from src.models import (
    ExperienceSummary,
    ExperienceV2,
    StrategyScore,
    TradeAttribution,
)


def test_experience_v2_columns():
    cols = set(ExperienceV2.__table__.columns.keys())
    assert {
        "account_id", "trade_id", "symbol", "regime_at_open",
        "strategy_mode", "factor_snapshot_at_open_id", "pnl_pct",
        "hold_duration", "exit_reason",
    } <= cols


def test_experience_v2_account_id_has_no_silent_default():
    col = ExperienceV2.__table__.columns["account_id"]
    assert col.default is None
    assert col.nullable is False


def test_experience_summary_has_no_embedding_in_v01():
    cols = set(ExperienceSummary.__table__.columns.keys())
    assert "summary_text" in cols
    assert "embedding" not in cols, "pgvector deferred to V0.2"


def test_trade_attribution_columns():
    cols = set(TradeAttribution.__table__.columns.keys())
    assert {
        "trade_id", "by_symbol", "by_time_bucket", "by_exit_reason",
        "by_factors_json", "factor_contributions_json",
    } <= cols


def test_strategy_score_composite_key_columns():
    cols = set(StrategyScore.__table__.columns.keys())
    assert {"strategy_mode", "symbol", "regime", "window", "win_rate", "sharpe"} <= cols


def test_strategy_score_has_unique_composite_index():
    # StrategyScore keys roll up per (account_id, strategy_mode, symbol, regime, window)
    idx_names = {i.name for i in StrategyScore.__table__.indexes}
    assert "ix_strategy_scores_key" in idx_names
    idx = next(i for i in StrategyScore.__table__.indexes if i.name == "ix_strategy_scores_key")
    assert idx.unique is True


def test_strategy_score_account_id_has_no_silent_default():
    col = StrategyScore.__table__.columns["account_id"]
    assert col.default is None
    assert col.nullable is False
