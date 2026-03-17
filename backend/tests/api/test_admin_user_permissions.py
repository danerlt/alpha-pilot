from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app.main import app
from src.shared.db import get_db
from src.shared.models.audit_log import AuditLog
from src.shared.models.base import Base
from src.shared.models.user import User


@pytest.fixture
def admin_user_perm_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine, tables=[User.__table__, AuditLog.__table__])
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.mark.asyncio
async def test_admin_user_list_requires_admin(admin_user_perm_db, monkeypatch):
    from src.app import router as router_module

    monkeypatch.setattr(
        router_module,
        "get_current_user",
        lambda: SimpleNamespace(id=2, username="user", role="user", status="active"),
    )

    def override_db():
        yield admin_user_perm_db

    app.dependency_overrides[get_db] = override_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/admin/users")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code in {401, 403}


@pytest.mark.asyncio
async def test_admin_user_update_requires_admin(admin_user_perm_db, monkeypatch):
    from src.app import router as router_module

    monkeypatch.setattr(
        router_module,
        "get_current_user",
        lambda: SimpleNamespace(id=3, username="user", role="user", status="active"),
    )

    def override_db():
        yield admin_user_perm_db

    app.dependency_overrides[get_db] = override_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch("/api/admin/users/123", json={"status": "disabled"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code in {401, 403}


@pytest.mark.asyncio
async def test_admin_update_user_returns_404_for_missing_user(admin_user_perm_db):
    from src.app import router as router_module

    def override_db():
        yield admin_user_perm_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[router_module.require_admin] = lambda: type("Admin", (), {"id": 77})()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch("/api/admin/users/999", json={"role": "admin"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
    assert admin_user_perm_db.query(AuditLog).count() == 0
