"""Auth router tests.

post-Plan5 安全审计 C5: 公开 register 已禁用, 改为预先在 DB seed admin
然后测 login + me. register 端点测试改为验证它返 403.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.services.auth import hash_password
from src.shared.db import get_db
from src.shared.enums import UserRole, UserStatus
from src.models.base import Base
from src.models.user import User


@pytest.fixture
def auth_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine, tables=[User.__table__])
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def _seed_user(
    db, *, email="alice@example.com", username="alice",
    password="strongpass123", role=UserRole.USER.value,
):
    user = User(
        username=username, email=email,
        password_hash=hash_password(password),
        role=role, status=UserStatus.ACTIVE.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_login_and_me_with_seeded_user(auth_db):
    """admin 引导后, login 拿 token, /me 拿当前用户."""
    _seed_user(auth_db)

    def override_db():
        yield auth_db

    app.dependency_overrides[get_db] = override_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            login_response = await client.post(
                "/api/auth/login",
                json={"email": "alice@example.com", "password": "strongpass123"},
            )
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]

            me_response = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert me_response.status_code == 200
            data = me_response.json()
            assert data["username"] == "alice"
            assert data["role"] == "user"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_public_register_is_disabled(auth_db):
    """post-Plan5 安全审计 C5: /api/auth/register 必须返 403, 不允许公开注册."""
    def override_db():
        yield auth_db

    app.dependency_overrides[get_db] = override_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                "/api/auth/register",
                json={"username": "anyone", "email": "anyone@example.com", "password": "strongpass123"},
            )
            assert r.status_code == 403, f"got {r.status_code}: {r.text}"
            # 没真创建 user
            assert auth_db.query(User).count() == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(auth_db):
    _seed_user(auth_db)

    def override_db():
        yield auth_db

    app.dependency_overrides[get_db] = override_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                "/api/auth/login",
                json={"email": "alice@example.com", "password": "wrong-password-1234"},
            )
            assert r.status_code == 401
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_unknown_email_returns_401(auth_db):
    """不要泄露用户存在性 — unknown email 也返 401, 不是 404."""
    def override_db():
        yield auth_db

    app.dependency_overrides[get_db] = override_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                "/api/auth/login",
                json={"email": "nobody@example.com", "password": "any-password-12345"},
            )
            assert r.status_code == 401
    finally:
        app.dependency_overrides.clear()
