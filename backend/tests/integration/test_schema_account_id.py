"""Verifies that all business tables have account_id column after migration 0001.

Uses SQLAlchemy's inspector to introspect the live schema.
"""
from __future__ import annotations

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from testcontainers.postgres import PostgresContainer

REQUIRED_TABLES = [
    "accounts",
    "risk_profiles",
    "parameter_versions",
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


@pytest.fixture(scope="module")
def pg_engine():
    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url()
        engine = create_engine(url)
        # Resolve both the ini file AND the script_location to absolute paths
        # so the test works regardless of pytest CWD (repo root or backend/).
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        cfg = Config(os.path.join(backend_dir, "src", "db", "alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", url)
        cfg.set_main_option("script_location", os.path.join(backend_dir, "src", "db", "migrations"))
        command.upgrade(cfg, "head")
        yield engine


def test_all_business_tables_have_account_id(pg_engine):
    inspector = inspect(pg_engine)
    existing = set(inspector.get_table_names())
    missing = [t for t in REQUIRED_TABLES if t not in existing]
    assert not missing, f"missing tables after migration: {missing}"

    tables_that_need_account_id = [t for t in REQUIRED_TABLES if t != "accounts"]
    for table in tables_that_need_account_id:
        cols = {c["name"] for c in inspector.get_columns(table)}
        assert "account_id" in cols, f"{table} missing account_id column"


def test_default_account_row_exists(pg_engine):
    from sqlalchemy import text
    with pg_engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, owner_user_id, name, enabled FROM accounts WHERE id = 1")
        ).first()
        assert row is not None, "default account (id=1) not bootstrapped"
        assert row.enabled is True
