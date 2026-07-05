"""RBAC 对照测试 (roadmap P4 验收): 权限矩阵与端点守卫一致。"""
from __future__ import annotations

import os
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.app import app
from src.controllers.dependencies import get_adapter, get_current_user
from src.db.session import get_db
from src.models import Base
from src.services.system.permissions import has_permission
from tests.unit.execution.test_manual_trade import _StubAdapter

_BUY = {
    "symbol": "BTCUSDT", "side": "BUY", "type": "MARKET",
    "qty": 0.02, "sl": 49_900.0, "tp": 50_500.0, "reduce_only": False,
}

# (method, path, body, 权限键) — 端点守卫应与矩阵一致
_GUARDED = [
    ("POST", "/api/orders/precheck", _BUY, "trade.manual_order"),
    ("POST", "/api/commands/pause", {"reason": "t"}, "trade.engine_toggle"),
]


def _client(role: str) -> TestClient:
    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)

    def _override():
        s = Session(eng)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="u", role=role, status="active",
    )
    app.dependency_overrides[get_adapter] = lambda: _StubAdapter()
    return TestClient(app)


@pytest.fixture(autouse=True)
def _cleanup():
    yield
    app.dependency_overrides.clear()


@pytest.mark.parametrize("role", ["owner", "admin", "trader", "viewer", "user"])
@pytest.mark.parametrize("method,path,body,perm", _GUARDED)
def test_endpoint_guard_matches_matrix(role, method, path, body, perm):
    """矩阵说可以 → 端点不 403; 矩阵说不行 → 端点必 400004。"""
    cli = _client(role)
    r = cli.request(method, path, json=body)
    allowed = has_permission(role, perm)
    if allowed:
        assert r.json().get("code") != "400004", f"{role} 应有 {perm} 却被拒: {path}"
    else:
        assert r.json().get("code") == "400004", f"{role} 不应有 {perm} 却放行: {path}"


def test_viewer_cannot_trade():
    """roadmap P4 验收: viewer 账户调交易接口返回 403 (业务码 400004)。"""
    cli = _client("viewer")
    assert cli.post("/api/orders", json=_BUY).json()["code"] == "400004"
    assert cli.patch("/api/positions/1/sltp", json={"stop_loss": 1.0}).json()["code"] == "400004"
    assert cli.post("/api/commands/close-all", json={
        "confirmation": "CLOSE ALL", "reason": "t",
        "account_id": 1, "trading_mode": "testnet",
    }).json()["code"] == "400004"


def test_trader_can_precheck_but_not_settings():
    cli = _client("trader")
    r = cli.post("/api/orders/precheck", json=_BUY)
    assert r.json().get("code") != "400004"  # trader 可预检 (可能因缺数据业务失败, 但不是权限拒)
    assert cli.get("/api/settings/exchange").json()["code"] == "400004"  # settings 仍 admin+


def test_owner_passes_admin_gate():
    cli = _client("owner")
    r = cli.get("/api/settings/exchange")
    assert r.json().get("code") != "400004"


def test_pending_user_approve_flow():
    """roadmap P4 验收: pending 用户批准流走通; owner/自身不可改。"""
    from src.models.user import User
    from src.services.auth import hash_password

    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)
    with Session(eng) as s:
        s.add(User(id=1, username="boss", email="boss@t", password_hash=hash_password("x" * 10), role="owner", status="active"))
        s.add(User(id=2, username="adm", email="adm@t", password_hash=hash_password("x" * 10), role="admin", status="active"))
        s.add(User(id=3, username="newbie", email="new@t", password_hash=hash_password("x" * 10), role="viewer", status="pending"))
        s.commit()

    def _override():
        s = Session(eng)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=2, username="adm", role="admin", status="active",
    )
    cli = TestClient(app)
    # 批准 pending
    r = cli.post("/api/admin/users/3/approve")
    assert r.json()["success"] is True
    assert r.json()["data"]["status"] == "active"
    # 重复批准 → 业务错
    assert cli.post("/api/admin/users/3/approve").json()["success"] is False
    # 不能动 owner
    assert cli.patch("/api/admin/users/1", json={"role": "viewer"}).json()["code"] == "400004"
    # 不能动自己
    assert cli.patch("/api/admin/users/2", json={"status": "disabled"}).json()["code"] == "400004"
    # 不能授予 owner
    assert cli.patch("/api/admin/users/3", json={"role": "owner"}).json()["code"] == "400004"
