"""event_bus_tables

Revision ID: b338184343a4
Revises: aa150ff7dee5
Create Date: 2026-04-23 20:17:13.987494

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b338184343a4'
down_revision: Union[str, None] = 'aa150ff7dee5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UTC_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "event_inbox",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("consumer_name", sa.String(length=80), nullable=False),
        sa.Column("event_id", sa.String(length=40), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )
    op.create_index(
        "ix_event_inbox_consumer_name_event_id",
        "event_inbox",
        ["consumer_name", "event_id"],
        unique=True,
    )

    op.create_table(
        "event_outbox",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("aggregate_type", sa.String(length=40), nullable=False),
        sa.Column("aggregate_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("event_id", sa.String(length=40), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )
    # Partial index on unpublished rows — the shuttle worker polls these.
    op.execute(
        "CREATE INDEX ix_event_outbox_unpublished "
        "ON event_outbox (id) WHERE published_at IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_event_outbox_unpublished")
    op.drop_table("event_outbox")
    op.drop_index("ix_event_inbox_consumer_name_event_id", table_name="event_inbox")
    op.drop_table("event_inbox")
