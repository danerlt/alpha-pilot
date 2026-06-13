from __future__ import annotations

from src.models import AgentInvocation, DecisionReview, PromptTemplate, ProposalDraft


def test_prompt_template_unique_name_version():
    idx_names = {i.name for i in PromptTemplate.__table__.indexes}
    assert any("ix_prompt_templates_name_version" in name for name in idx_names)


def test_proposal_draft_fks():
    cols = ProposalDraft.__table__.columns
    assert "template_id" in cols
    assert "context_hash" in cols
    assert "rendered_system" in cols
    assert "rendered_user" in cols


def test_proposal_draft_account_id_has_no_silent_default():
    col = ProposalDraft.__table__.columns["account_id"]
    assert col.default is None, "ProposalDraft.account_id must NOT have a silent default"
    assert col.nullable is False


def test_decision_review_result_column():
    cols = DecisionReview.__table__.columns
    assert "decision_id" in cols
    assert "reviewer_type" in cols
    assert "result" in cols
    assert "adjustments_json" in cols


def test_agent_invocation_core_columns():
    cols = set(AgentInvocation.__table__.columns.keys())
    assert {
        "agent_type",
        "input_hash",
        "prompt_template_id",
        "llm_provider",
        "llm_model",
        "tokens_used",
        "latency_ms",
        "outcome",
    } <= cols


def test_agent_invocation_account_id_has_no_silent_default():
    col = AgentInvocation.__table__.columns["account_id"]
    assert col.default is None, "AgentInvocation.account_id must NOT have a silent default"
    assert col.nullable is False
