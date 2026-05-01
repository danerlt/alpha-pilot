"""验证 BaseCrud 行为（用真 PG fixture）。"""
import pytest

from src.common.exception.errors import DBException
from src.cruds.user_crud import user_crud
from src.models import Base


@pytest.fixture
def pg_session_with_schema(pg_engine):
    """创建 schema + 提供 session（每 test 独立 schema）。"""
    from sqlalchemy.orm import sessionmaker

    Base.metadata.create_all(pg_engine)
    SessionLocal = sessionmaker(bind=pg_engine, autocommit=False, autoflush=False, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(pg_engine)


def test_get_or_none_returns_none_when_not_exists(pg_session_with_schema):
    assert user_crud.get_or_none(pg_session_with_schema, 999999) is None


def test_get_raises_db_exception_when_not_exists(pg_session_with_schema):
    with pytest.raises(DBException):
        user_crud.get(pg_session_with_schema, 999999)


def test_add_and_get(pg_session_with_schema):
    u = user_crud.add(
        pg_session_with_schema,
        username="alice",
        email="alice@x.com",
        password_hash="hash",
        role="admin",
        status="active",
    )
    pg_session_with_schema.commit()
    assert u.id > 0
    fetched = user_crud.get(pg_session_with_schema, u.id)
    assert fetched.username == "alice"


def test_update(pg_session_with_schema):
    u = user_crud.add(
        pg_session_with_schema,
        username="bob",
        email="bob@x.com",
        password_hash="hash",
        role="user",
        status="active",
    )
    pg_session_with_schema.commit()
    user_crud.update(pg_session_with_schema, u.id, username="bob_updated")
    pg_session_with_schema.commit()
    assert user_crud.get(pg_session_with_schema, u.id).username == "bob_updated"


def test_soft_delete(pg_session_with_schema):
    u = user_crud.add(
        pg_session_with_schema,
        username="carol",
        email="carol@x.com",
        password_hash="hash",
        role="user",
        status="active",
    )
    pg_session_with_schema.commit()
    user_crud.delete(pg_session_with_schema, u.id)
    pg_session_with_schema.commit()
    fetched = user_crud.get(pg_session_with_schema, u.id)
    assert fetched.delete_flag is True  # 软删
