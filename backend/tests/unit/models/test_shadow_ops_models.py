from __future__ import annotations

from src.models import OpsDiagnosis, ShadowDecision, ShadowEvaluation


def test_shadow_decision_columns():
    cols = set(ShadowDecision.__table__.columns.keys())
    assert {"shadow_run_id", "real_decision_id", "proposal_json", "parameter_version_id"} <= cols


def test_shadow_evaluation_columns():
    cols = set(ShadowEvaluation.__table__.columns.keys())
    assert {"shadow_decision_id", "real_trade_id", "shadow_pnl_sim", "real_pnl", "diff"} <= cols


def test_ops_diagnosis_columns():
    cols = set(OpsDiagnosis.__table__.columns.keys())
    assert {"triggered_by_event_id", "severity", "pattern_matched", "llm_narrative"} <= cols


def test_shadow_decision_has_shadow_run_index():
    idx_names = {i.name for i in ShadowDecision.__table__.indexes}
    assert "ix_shadow_decisions_shadow_run_id" in idx_names
