"""add users table

Revision ID: 20260317_0003
Revises: 20260317_0002
Create Date: 2026-03-17 09:55:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260317_0003"
down_revision: Union[str, Sequence[str], None] = "20260317_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UTC_NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=50), nullable=False, unique=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="user"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("last_login_at", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )


def downgrade() -> None:
    op.drop_table("users")
