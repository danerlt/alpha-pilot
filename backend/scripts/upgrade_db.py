"""运行所有待执行的 Alembic 迁移，并兼容旧版 create_all 初始化的数据库。"""
import os
import subprocess
import sys

from sqlalchemy import create_engine, inspect, text

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.config import get_base_settings

LEGACY_TABLES = {
    "account_snapshots",
    "ai_decisions",
    "candles",
    "daily_reports",
    "experience_store",
    "indicator_snapshots",
    "orders",
    "positions",
    "regime_snapshots",
    "risk_events",
    "trades",
}
INITIAL_REVISION = "20260316_0001"


def _needs_legacy_stamp(database_url: str) -> bool:
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        if not LEGACY_TABLES.issubset(tables):
            return False
        if "alembic_version" not in tables:
            return False
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar()
        return version is None
    finally:
        engine.dispose()


def main():
    settings = get_base_settings()
    print("Running pending migrations...")

    if _needs_legacy_stamp(settings.DATABASE_URL):
        print(f"Detected legacy schema without Alembic version; stamping {INITIAL_REVISION} before upgrade...")
        subprocess.run(["alembic", "stamp", INITIAL_REVISION], check=True)

    subprocess.run(["alembic", "upgrade", "head"], check=True)
    print("Migrations complete.")


if __name__ == "__main__":
    main()
