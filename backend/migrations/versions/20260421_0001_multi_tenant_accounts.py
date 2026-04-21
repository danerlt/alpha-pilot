"""multi-tenant foundation: accounts, risk_profiles, parameter_versions, account_id FKs

Revision ID: 20260421_0001
Revises: 20260317_0004
Create Date: 2026-04-21 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260421_0001"
down_revision: Union[str, Sequence[str], None] = "20260317_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UTC_NOW = sa.text("CURRENT_TIMESTAMP")

EXISTING_TABLES_NEEDING_ACCOUNT_ID = [
    "positions",
    "orders",
    "trades",
    "candles",
    "indicator_snapshots",
    "regime_snapshots",
    "account_snapshots",
    "ai_decisions",
    "risk_events",
    "experience_store",
    "daily_reports",
    "symbol_configs",
    "audit_logs",
]


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("exchange", sa.String(length=20), nullable=False, server_default="binance"),
        sa.Column("trading_mode", sa.String(length=10), nullable=False, server_default="testnet"),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("api_secret_encrypted", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("risk_profile_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
    )

    op.create_table(
        "risk_profiles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        # No server_default on fresh-table account_id — every insert must
        # specify it explicitly. server_default=1 is only used on retrofits
        # (ALTER TABLE ADD COLUMN) to backfill existing rows.
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("max_position_size_pct", sa.Numeric(5, 4), nullable=False, server_default="0.20"),
        sa.Column("max_daily_loss_pct", sa.Numeric(5, 4), nullable=False, server_default="0.03"),
        sa.Column("max_consecutive_losses", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("max_single_risk_pct", sa.Numeric(5, 4), nullable=False, server_default="0.01"),
        sa.Column("min_rr_ratio", sa.Numeric(5, 2), nullable=False, server_default="1.5"),
        sa.Column("sl_atr_min_mult", sa.Numeric(5, 2), nullable=False, server_default="0.5"),
        sa.Column("sl_atr_max_mult", sa.Numeric(5, 2), nullable=False, server_default="5.0"),
        sa.Column("regime_thresholds_json", sa.JSON(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_risk_profiles_account"),
    )

    op.create_table(
        "parameter_versions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        # No server_default — fresh table; see risk_profiles comment above.
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("profile_id", sa.BigInteger(), nullable=True),
        sa.Column("change_type", sa.String(length=40), nullable=False),
        sa.Column("old_value_json", sa.JSON(), nullable=True),
        sa.Column("new_value_json", sa.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("proposed_by_agent", sa.String(length=40), nullable=True),
        sa.Column("validated_by", sa.String(length=40), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_parameter_versions_account"),
        sa.ForeignKeyConstraint(["profile_id"], ["risk_profiles.id"], name="fk_parameter_versions_profile"),
    )

    op.execute(
        "INSERT INTO accounts (id, name, exchange, trading_mode, enabled) "
        "VALUES (1, 'default', 'binance', 'testnet', TRUE) "
        "ON CONFLICT (id) DO NOTHING"
    )
    op.execute(
        "INSERT INTO risk_profiles (id, account_id, name, active) "
        "VALUES (1, 1, 'default', TRUE) "
        "ON CONFLICT (id) DO NOTHING"
    )
    op.execute("UPDATE accounts SET risk_profile_id = 1 WHERE id = 1")

    for table in EXISTING_TABLES_NEEDING_ACCOUNT_ID:
        op.add_column(
            table,
            sa.Column("account_id", sa.BigInteger(), nullable=False, server_default="1"),
        )
        op.create_foreign_key(
            f"fk_{table}_account", table, "accounts", ["account_id"], ["id"]
        )
        op.create_index(f"ix_{table}_account_id", table, ["account_id"])


def downgrade() -> None:
    for table in EXISTING_TABLES_NEEDING_ACCOUNT_ID:
        op.drop_index(f"ix_{table}_account_id", table_name=table)
        op.drop_constraint(f"fk_{table}_account", table, type_="foreignkey")
        op.drop_column(table, "account_id")
    op.drop_table("parameter_versions")
    op.drop_table("risk_profiles")
    op.drop_table("accounts")
