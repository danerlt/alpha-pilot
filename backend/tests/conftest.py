"""pytest 共享 fixture / 启动 hook.

ALPHAPILOT_SKIP_SECRET_VALIDATION=1: 所有测试默认跳过 config._validate_secrets,
让 SQLite in-memory 单测不需要配 .env 真随机密钥. 这只在测试运行环境生效.
生产 / dev-server 不应设此环境变量.
"""
from __future__ import annotations

import os

# 必须在 import src.shared.config 之前设
os.environ.setdefault("ALPHAPILOT_SKIP_SECRET_VALIDATION", "1")

import logging

import pytest


@pytest.fixture(autouse=True)
def _silence_app_exception_autolog(monkeypatch):
    """单测全局静音 AppBaseException auto_log，避免日志污染输出。

    需要验证 auto_log 行为的单测可以临时 ``monkeypatch.setattr(AppBaseException, "auto_log", True)``
    覆盖回来。
    """
    try:
        from src.common.exception.errors import AppBaseException

        monkeypatch.setattr(AppBaseException, "auto_log", False)
    except ImportError:
        # 阶段 1 早期 src.common 还没建好的情况
        pass


@pytest.fixture(autouse=True)
def _reset_logger_disabled_state():
    """一些 test（如 testcontainers 的 alembic.runtime.migration 用法）会临时禁用 logger，
    导致后续测试的 caplog / 自定义 handler 抓不到。每个 test 跑前重置。
    """
    target_loggers = (
        "app.exception",
        "middleware.request",
        "middleware.error",
        "app",
        "alembic",
        "alembic.runtime.migration",
    )
    for name in target_loggers:
        lg = logging.getLogger(name)
        lg.disabled = False
        lg.propagate = True
    yield


# ── Stage 2/3: 真 PostgreSQL fixture（取代 sqlite in-memory 测试）─────────────────
# 优化：复用本地已运行的 docker postgres (alpha-pilot-postgres-1, 5442)，
# 避免 testcontainers 每个 session 启停 PG 容器的开销。
_TEST_DB_NAME = "alphapilot_test"
_TEST_DB_URL = f"postgresql+psycopg2://alphapilot:alphapilot@localhost:5442/{_TEST_DB_NAME}"
_TEST_ENGINE = None  # session-global，单 engine 服务所有 truncate


def _ensure_test_database():
    """创建 alphapilot_test DB（如不存在）+ 应用 alembic upgrade head。"""
    import subprocess
    from sqlalchemy import create_engine, text

    # 1. 用 alphapilot 默认库连接，确保 test DB 存在
    admin_url = "postgresql+psycopg2://alphapilot:alphapilot@localhost:5442/alphapilot"
    admin_eng = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_eng.connect() as conn:
        exists = conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{_TEST_DB_NAME}'")
        ).first()
        if not exists:
            conn.execute(text(f"CREATE DATABASE {_TEST_DB_NAME}"))
    admin_eng.dispose()

    # 2. 应用 alembic 到 test DB
    env = os.environ.copy()
    env["DATABASE_URL"] = _TEST_DB_URL
    env["ALPHAPILOT_SKIP_SECRET_VALIDATION"] = "1"
    subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        env=env,
        check=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        capture_output=True,
    )


@pytest.fixture(autouse=True, scope="session")
def _set_test_database_url() -> "str":
    """Session-scoped autouse：确保 test DB 存在 + alembic 应用 + TEST_DATABASE_URL 设置。"""
    _ensure_test_database()
    os.environ["TEST_DATABASE_URL"] = _TEST_DB_URL
    yield _TEST_DB_URL


def _get_test_engine():
    """复用单 engine 用于 truncate（避免每个测试新建 engine 的开销）。"""
    global _TEST_ENGINE
    if _TEST_ENGINE is None:
        from sqlalchemy import create_engine

        _TEST_ENGINE = create_engine(_TEST_DB_URL, pool_pre_ping=True)
    return _TEST_ENGINE


@pytest.fixture(scope="session")
def pg_container_url(_set_test_database_url) -> str:
    """保留兼容名字。"""
    return _set_test_database_url


@pytest.fixture(autouse=True)
def _truncate_all_pg_tables_after_each_test(_set_test_database_url):
    """每个测试结束后 TRUNCATE 所有表（保留 schema）。

    为避免测试遗漏 close session 导致 TRUNCATE 阻塞，先 ``SET LOCAL lock_timeout = '3s'``
    让 TRUNCATE 在 3 秒内拿不到 ACCESS EXCLUSIVE 锁就失败（不 hang 测试套件）。
    """
    yield
    try:
        from sqlalchemy import text

        engine = _get_test_engine()
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL lock_timeout = '3s'"))
            result = conn.execute(text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename != 'alembic_version'"
            ))
            tables = [row[0] for row in result]
            if tables:
                # 用 DELETE 而不是 TRUNCATE：DELETE 拿 ROW EXCLUSIVE 锁，
                # 不等其他 session 结束（避免 hang）。性能对 100 行级测试数据可接受。
                # 顺序：先删带外键引用的表（CASCADE 会自动跟着删被引用表，但本项目无外键）
                for t in tables:
                    conn.execute(text(f'DELETE FROM "{t}"'))
    except Exception:
        # 容器还没起 / 没建表 / lock timeout / 测试本身没碰 PG —— 都忽略
        pass


@pytest.fixture
def pg_engine(_set_test_database_url):
    """Function-scoped engine（轻量；连同 session 用同一 PG 实例）。"""
    from sqlalchemy import create_engine

    engine = create_engine(_set_test_database_url, pool_pre_ping=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def pg_session(pg_engine):
    """Function-scoped session。"""
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=pg_engine, autocommit=False, autoflush=False, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
