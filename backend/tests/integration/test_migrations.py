import pytest
from sqlalchemy import create_engine, inspect
from testcontainers.postgres import PostgresContainer
from alembic.config import Config
from alembic import command
import os


@pytest.fixture(scope="module")
def migrated_db():
    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url()
        # 运行所有迁移
        alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "../../alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", url)
        command.upgrade(alembic_cfg, "head")
        engine = create_engine(url)
        yield engine


def test_all_tables_created(migrated_db):
    inspector = inspect(migrated_db)
    tables = inspector.get_table_names()
    expected = [
        "candles", "account_snapshots", "indicator_snapshots",
        "regime_snapshots", "positions", "ai_decisions",
        "orders", "trades", "risk_events", "experience_store", "daily_reports", "system_settings", "users",
    ]
    for table in expected:
        assert table in tables, f"Table '{table}' not found in DB"


def test_all_tables_have_trading_mode(migrated_db):
    """所有表均含 trading_mode 列"""
    inspector = inspect(migrated_db)
    tables_requiring_trading_mode = [
        "candles", "account_snapshots", "indicator_snapshots", "regime_snapshots",
        "positions", "ai_decisions", "orders", "trades",
        "risk_events", "experience_store", "daily_reports",
    ]
    for table in tables_requiring_trading_mode:
        cols = {c["name"] for c in inspector.get_columns(table)}
        assert "trading_mode" in cols, f"Table '{table}' missing trading_mode column"


def test_candles_unique_index(migrated_db):
    inspector = inspect(migrated_db)
    indexes = inspector.get_indexes("candles")
    index_names = [i["name"] for i in indexes]
    assert "ix_candles_symbol_timeframe_open_time" in index_names


def test_orders_trace_id_unique_constraint(migrated_db):
    inspector = inspect(migrated_db)
    unique_constraints = inspector.get_unique_constraints("orders")
    columns = [tuple(c["column_names"]) for c in unique_constraints]
    assert ("trace_id",) in columns


def test_system_settings_unique_key_constraint(migrated_db):
    inspector = inspect(migrated_db)
    unique_constraints = inspector.get_unique_constraints("system_settings")
    columns = [tuple(c["column_names"]) for c in unique_constraints]
    assert ("key",) in columns
