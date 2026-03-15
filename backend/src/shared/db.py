from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.shared.config import get_settings

# 模块级单例，确保连接池只创建一次
_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(get_settings().DATABASE_URL, pool_pre_ping=True)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        # SQLAlchemy 2.x: engine 作为第一个位置参数，不用 bind=
        _SessionLocal = sessionmaker(get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


def get_db() -> Session:
    """FastAPI 依赖注入用"""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
