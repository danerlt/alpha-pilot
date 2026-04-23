from __future__ import annotations

from src.shared.models import AIDecision


def test_ai_decision_has_extended_columns():
    cols = set(AIDecision.__table__.columns.keys())
    required = {
        "proposal_draft_id",
        "llm_provider",
        "llm_model",
        "tokens_used",
        "latency_ms",
        "source",
        "factor_snapshot_id",
    }
    missing = required - cols
    assert not missing, f"missing columns: {missing}"


def test_source_column_is_not_null():
    col = AIDecision.__table__.columns["source"]
    assert col.nullable is False


def test_source_default_is_ai_trader():
    col = AIDecision.__table__.columns["source"]
    # Check either Python default or server_default represents "ai_trader"
    default_str = ""
    if col.default is not None:
        default_str = str(col.default.arg)
    server_default_str = ""
    if col.server_default is not None:
        server_default_str = str(col.server_default.arg)
    assert "ai_trader" in default_str or "ai_trader" in server_default_str, (
        f"source default should be 'ai_trader', got default={default_str!r} "
        f"server_default={server_default_str!r}"
    )


def test_optional_llm_fields_are_nullable():
    for name in ["proposal_draft_id", "llm_provider", "llm_model",
                 "tokens_used", "latency_ms", "factor_snapshot_id"]:
        col = AIDecision.__table__.columns[name]
        assert col.nullable is True, f"{name} should be nullable"
