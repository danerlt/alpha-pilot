import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app.main import app
from src.shared.db import get_db
from src.shared.models.base import Base
from src.shared.models.user import User


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


@pytest.mark.asyncio
async def test_register_login_and_me(auth_db):
    def override_db():
        yield auth_db

    app.dependency_overrides[get_db] = override_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            register_response = await client.post(
                "/api/auth/register",
                json={"username": "alice", "email": "alice@example.com", "password": "strongpass123"},
            )
            assert register_response.status_code == 200
            token = register_response.json()["access_token"]

            login_response = await client.post(
                "/api/auth/login",
                json={"email": "alice@example.com", "password": "strongpass123"},
            )
            assert login_response.status_code == 200

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
async def test_register_rejects_duplicate_email(auth_db):
    def override_db():
        yield auth_db

    app.dependency_overrides[get_db] = override_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post(
                "/api/auth/register",
                json={"username": "alice", "email": "alice@example.com", "password": "strongpass123"},
            )
            duplicate = await client.post(
                "/api/auth/register",
                json={"username": "alice2", "email": "alice@example.com", "password": "strongpass123"},
            )
            assert duplicate.status_code == 409
    finally:
        app.dependency_overrides.clear()
