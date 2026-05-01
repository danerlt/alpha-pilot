"""PostgreSQL 同步 engine + SessionLocal 单例。

特性：
- pool_pre_ping=True：取连接前 ping，避免使用断开的空闲连接
- pool_recycle=3600：1 小时回收一次连接
- expire_on_commit=False：commit 后不 expire ORM 对象（commit/refresh 由 service 显式控制）
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from src.configs import get_app_config
from src.utils.json import dumps as _json_dumps


def _make_engine(uri: str, echo: bool) -> Engine:
    """创建 PostgreSQL engine（v3.7：彻底删除 sqlite 兼容路径）。"""
    cfg = get_app_config()
    return create_engine(
        uri,
        echo=echo,
        json_serializer=_json_dumps,
        pool_size=cfg.POOL_SIZE,
        max_overflow=cfg.POOL_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={"connect_timeout": cfg.DB_CONNECT_TIMEOUT},
    )


_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        cfg = get_app_config()
        _engine = _make_engine(cfg.db_uri, echo=cfg.PRINT_SQL)
    return _engine


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SessionLocal


def reset_engine() -> None:
    """单测使用：销毁 engine 单例。"""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


# 兼容老代码暴露的常量名（lazy 初始化）
def __getattr__(name: str):
    if name == "sync_engine":
        return get_engine()
    if name == "SessionLocal":
        return get_session_factory()
    raise AttributeError(name)
