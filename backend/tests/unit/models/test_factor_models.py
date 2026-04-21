from __future__ import annotations

from src.shared.models import FactorCandidate, FactorDefinition, FactorSnapshot


def test_factor_definition_has_core_columns():
    cols = set(FactorDefinition.__table__.columns.keys())
    assert {"id", "name", "version", "inputs_json", "description", "formula_code_ref", "active"} <= cols


def test_factor_snapshot_unique_key():
    cols = FactorSnapshot.__table__.columns
    assert "account_id" in cols
    assert "symbol" in cols
    assert "timeframe" in cols
    assert "open_time" in cols
    assert "factors_json" in cols


def test_factor_snapshot_account_id_has_no_silent_default():
    # FactorSnapshot is a fresh table; callers must pass account_id explicitly.
    col = FactorSnapshot.__table__.columns["account_id"]
    assert col.default is None, "FactorSnapshot.account_id must NOT have a silent default"
    assert col.nullable is False


def test_factor_candidate_exists_for_v03():
    cols = set(FactorCandidate.__table__.columns.keys())
    assert {"id", "proposed_by_agent", "name", "validation_status"} <= cols
