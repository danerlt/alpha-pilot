"""GET /api/admin/audit-logs 集成测试 (BE-4/TEST-3 补强)。

覆盖: 倒序排序 / limit clamp / actor 用户名映射 / 匿名拒绝。
"""
from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app import app
from src.db.session import get_db
from src.models.audit_log import AuditLog
from src.models.base import Base
from src.models.user import User


@pytest.fixture
def audit_db():
    engine = create_engine(
        os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"),
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine, tables=[AuditLog.__table__, User.__table__])
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def _admin_override():
    return type("Admin", (), {"id": 1, "username": "admin", "role": "admin"})()


@pytest.mark.asyncio
async def test_audit_logs_ordered_desc_with_actor(audit_db):
    from src.controllers import router as router_module

    admin_user = User(
        username="admin", email="admin@example.com",
        password_hash="x", role="admin", status="active",
    )
    audit_db.add(admin_user)
    audit_db.flush()
    aid = admin_user.id
    # PG 测试库序列跨测试不重置, 不能假设 id=1
    audit_db.add_all([
        AuditLog(user_id=aid, action="create", resource_type="symbol_config", resource_id="1"),
        AuditLog(user_id=aid, action="update", resource_type="user", resource_id="2"),
        AuditLog(user_id=aid + 999_999, action="update", resource_type="user", resource_id="3"),
    ])
    audit_db.commit()

    def override_db():
        yield audit_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[router_module.require_admin] = _admin_override
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/admin/audit-logs")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 3
    # 倒序: id 最大的在最前
    ids = [row["id"] for row in data]
    assert ids == sorted(ids, reverse=True)
    # actor 用户名映射; 未知 user_id 留 None
    by_resource = {row["resource_id"]: row for row in data}
    assert by_resource["1"]["actor"] == "admin"
    assert by_resource["3"]["actor"] is None
    assert by_resource["3"]["user_id"] is not None


@pytest.mark.asyncio
async def test_audit_logs_limit_clamped_to_200(audit_db):
    from src.controllers import router as router_module

    audit_db.add_all([
        AuditLog(user_id=1, action="create", resource_type="symbol_config", resource_id=str(i))
        for i in range(205)
    ])
    audit_db.commit()

    def override_db():
        yield audit_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[router_module.require_admin] = _admin_override
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp_over = await client.get("/api/admin/audit-logs", params={"limit": 9999})
            resp_under = await client.get("/api/admin/audit-logs", params={"limit": 0})
    finally:
        app.dependency_overrides.clear()

    assert len(resp_over.json()["data"]) == 200
    assert len(resp_under.json()["data"]) == 1


@pytest.mark.asyncio
async def test_audit_logs_rejects_anonymous():
    """无鉴权依赖 override 时, 匿名访问 → AUTH_ERROR (HTTP 200 + 400003)。"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/admin/audit-logs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert body["code"] == "400003"
