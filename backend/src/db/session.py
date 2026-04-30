"""Session 工厂（双对外名）。

- ``get_db()``: generator，给 FastAPI ``Depends(get_db)`` / ``CurrentSession`` 用
- ``get_db_session()``: ``@contextmanager`` 包装，给 worker / scheduler / 脚本的 ``with`` 用
- 都不自动 commit；commit 由调用方显式处理；异常自动 rollback
"""
from __future__ import annotations

import contextlib
from collections.abc import Generator
from typing import Annotated, TypeAlias

from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.db.engines import get_session_factory


def get_db() -> Generator[Session, None, None]:
    """FastAPI Depends / generator 形态。"""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()


# `with` 语句形态（scheduler / 脚本 / EventShuttle）
get_db_session = contextlib.contextmanager(get_db)

# FastAPI 路由依赖注入
CurrentSession: TypeAlias = Annotated[Session, Depends(get_db)]
