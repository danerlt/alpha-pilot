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


# ── Stage 2: 真 PostgreSQL fixture（取代 sqlite in-memory 测试）─────────────────
@pytest.fixture(scope="session")
def pg_container_url() -> str:
    """Session-scoped 真 PostgreSQL 容器，所有 ORM 测试共用。

    使用 testcontainers 起 postgres:16-alpine。session 级别共用一个容器，
    避免每个 test 都启停。各 test 之间靠事务回滚做数据隔离。
    """
    from testcontainers.postgres import PostgresContainer

    pg = PostgresContainer("postgres:16-alpine")
    pg.start()
    try:
        url = pg.get_connection_url()
        # testcontainers 默认返回 postgresql+psycopg2://，与本项目一致
        if "+psycopg2" not in url and url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        yield url
    finally:
        pg.stop()


@pytest.fixture
def pg_engine(pg_container_url: str):
    """Function-scoped engine 绑定到 session pg；每个 test 跑完销毁。"""
    from sqlalchemy import create_engine

    engine = create_engine(pg_container_url, pool_pre_ping=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def pg_session(pg_engine):
    """Function-scoped session，自动 rollback（保证测试间数据隔离）。"""
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=pg_engine, autocommit=False, autoflush=False, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
