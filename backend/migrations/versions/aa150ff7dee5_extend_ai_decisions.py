"""extend_ai_decisions

Revision ID: aa150ff7dee5
Revises: d9076875486b
Create Date: 2026-04-23 20:04:50.346539

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa150ff7dee5'
down_revision: Union[str, None] = 'd9076875486b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ai_decisions", sa.Column("proposal_draft_id", sa.BigInteger(), nullable=True))
    op.add_column("ai_decisions", sa.Column("llm_provider", sa.String(length=30), nullable=True))
    op.add_column("ai_decisions", sa.Column("llm_model", sa.String(length=60), nullable=True))
    op.add_column("ai_decisions", sa.Column("tokens_used", sa.Integer(), nullable=True))
    op.add_column("ai_decisions", sa.Column("latency_ms", sa.Integer(), nullable=True))
    op.add_column(
        "ai_decisions",
        sa.Column("source", sa.String(length=20), nullable=False, server_default="ai_trader"),
    )
    op.add_column("ai_decisions", sa.Column("factor_snapshot_id", sa.BigInteger(), nullable=True))

    op.create_foreign_key(
        "fk_ai_decisions_proposal_draft",
        "ai_decisions",
        "proposal_drafts",
        ["proposal_draft_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_ai_decisions_factor_snapshot",
        "ai_decisions",
        "factor_snapshots",
        ["factor_snapshot_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_ai_decisions_factor_snapshot", "ai_decisions", type_="foreignkey")
    op.drop_constraint("fk_ai_decisions_proposal_draft", "ai_decisions", type_="foreignkey")
    op.drop_column("ai_decisions", "factor_snapshot_id")
    op.drop_column("ai_decisions", "source")
    op.drop_column("ai_decisions", "latency_ms")
    op.drop_column("ai_decisions", "tokens_used")
    op.drop_column("ai_decisions", "llm_model")
    op.drop_column("ai_decisions", "llm_provider")
    op.drop_column("ai_decisions", "proposal_draft_id")
