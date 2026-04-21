"""decision audit schema: prompt_templates, proposal_drafts, decision_reviews, agent_invocations

Revision ID: 20260421_0003
Revises: 20260421_0002
Create Date: 2026-04-22 00:00:01.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260421_0003"
down_revision: Union[str, Sequence[str], None] = "20260421_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UTC_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("system_template", sa.Text(), nullable=False),
        sa.Column("user_template", sa.Text(), nullable=False),
        sa.Column("variables_json", sa.JSON(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )
    op.create_index("ix_prompt_templates_name_version", "prompt_templates", ["name", "version"], unique=True)

    op.create_table(
        "proposal_drafts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        # Fresh table — no server_default on account_id.
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default="testnet"),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("template_id", sa.BigInteger(), nullable=True),
        sa.Column("context_hash", sa.String(length=64), nullable=False),
        sa.Column("rendered_system", sa.Text(), nullable=False),
        sa.Column("rendered_user", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_proposal_drafts_account"),
        sa.ForeignKeyConstraint(["template_id"], ["prompt_templates.id"], name="fk_proposal_drafts_template"),
    )

    op.create_table(
        "decision_reviews",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("decision_id", sa.BigInteger(), nullable=False),
        sa.Column("reviewer_type", sa.String(length=20), nullable=False),  # rule | ai
        sa.Column("result", sa.String(length=20), nullable=False),  # approve | adjust | reject
        sa.Column("adjustments_json", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["decision_id"], ["ai_decisions.id"], name="fk_decision_reviews_decision"),
    )

    op.create_table(
        "agent_invocations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        # Fresh table — no server_default on account_id.
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("agent_type", sa.String(length=30), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("prompt_template_id", sa.BigInteger(), nullable=True),
        sa.Column("llm_provider", sa.String(length=30), nullable=True),
        sa.Column("llm_model", sa.String(length=60), nullable=True),
        sa.Column("input_json", sa.JSON(), nullable=True),
        sa.Column("output_json", sa.JSON(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("outcome", sa.String(length=20), nullable=False, server_default="success"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_agent_invocations_account"),
    )
    op.create_index("ix_agent_invocations_occurred_at", "agent_invocations", ["occurred_at"])


def downgrade() -> None:
    # drop_table cascades indexes in PostgreSQL, but explicit drop_index first
    # keeps the intent clear and avoids DB-specific behavior assumptions.
    op.drop_index("ix_agent_invocations_occurred_at", table_name="agent_invocations")
    op.drop_table("agent_invocations")
    op.drop_table("decision_reviews")
    op.drop_table("proposal_drafts")
    op.drop_index("ix_prompt_templates_name_version", table_name="prompt_templates")
    op.drop_table("prompt_templates")
