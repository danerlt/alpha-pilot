"""向后兼容转发；新代码应直接 import src.db.session / src.db.engines。

阶段 2 全面迁移完成后本文件会被删除。
"""
from src.db.engines import (  # noqa: F401
    get_engine,
    get_session_factory,
    reset_engine,
)
from src.db.session import get_db, get_db_session  # noqa: F401


# 兼容老代码 from src.shared.db import sync_engine / SessionLocal
def __getattr__(name: str):
    if name == "sync_engine":
        return get_engine()
    if name == "SessionLocal":
        return get_session_factory()
    raise AttributeError(name)


__all__ = [
    "get_engine",
    "get_session_factory",
    "reset_engine",
    "get_db",
    "get_db_session",
]
