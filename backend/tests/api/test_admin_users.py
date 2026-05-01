import os
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app import app
from src.shared.db import get_db
from src.shared.enums import UserRole, UserStatus
from src.models.audit_log import AuditLog
from src.models.base import Base
from src.models.user import User


@pytest.fixture
def admin_users_db():
    engine = create_engine(
        os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"),
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
async def test_admin_can_list_users(admin_users_db):
    from src.api import router as router_module

    admin_users_db.add_all(
        [
            User(
                username="admin",
                email="admin@example.com",
                password_hash="secret-1",
                role=UserRole.ADMIN.value,
                status=UserStatus.ACTIVE.value,
            ),
            User(
                username="alice",
                email="alice@example.com",
                password_hash="secret-2",
                role=UserRole.USER.value,
                status=UserStatus.DISABLED.value,
            ),
        ]
    )
    admin_users_db.commit()

    def override_db():
        yield admin_users_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[router_module.require_admin] = lambda: type("Admin", (), {"id": 1})()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/admin/users")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert [item["username"] for item in data] == ["admin", "alice"]
    assert data[0]["role"] == "admin"
    assert data[1]["status"] == "disabled"
    assert "password_hash" not in data[0]


@pytest.mark.asyncio
async def test_admin_can_update_user_role_and_status_with_audit_log(admin_users_db):
    from src.api import router as router_module

    target_user = User(
        username="bob",
        email="bob@example.com",
        password_hash="secret-3",
        role=UserRole.USER.value,
        status=UserStatus.ACTIVE.value,
    )
    admin_users_db.add(target_user)
    admin_users_db.commit()
    admin_users_db.refresh(target_user)

    def override_db():
        yield admin_users_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[router_module.require_admin] = lambda: type("Admin", (), {"id": 99})()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                f"/api/admin/users/{target_user.id}",
                json={"role": "admin", "status": "disabled"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == target_user.id
    assert payload["role"] == "admin"
    assert payload["status"] == "disabled"

    refreshed = admin_users_db.query(User).filter(User.id == target_user.id).first()
    assert refreshed is not None
    assert refreshed.role == "admin"
    assert refreshed.status == "disabled"

    logs = admin_users_db.query(AuditLog).all()
    assert len(logs) == 1
    assert logs[0].user_id == 99
    assert logs[0].action == "update"
    assert logs[0].resource_type == "user"
    assert logs[0].resource_id == str(target_user.id)
    assert logs[0].before_json == {"role": "user", "status": "active"}
    assert logs[0].after_json == {"role": "admin", "status": "disabled"}


@pytest.mark.asyncio
async def test_admin_update_user_requires_at_least_one_change(admin_users_db):
    from src.api import router as router_module

    target_user = User(
        username="carol",
        email="carol@example.com",
        password_hash="secret-4",
        role=UserRole.USER.value,
        status=UserStatus.ACTIVE.value,
    )
    admin_users_db.add(target_user)
    admin_users_db.commit()
    admin_users_db.refresh(target_user)

    def override_db():
        yield admin_users_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[router_module.require_admin] = lambda: type("Admin", (), {"id": 88})()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(f"/api/admin/users/{target_user.id}", json={})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "No user fields provided"
    assert admin_users_db.query(AuditLog).count() == 0
