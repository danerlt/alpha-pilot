"""OpenAPI 契约测试 (webapp 架构 B1): operation_id 稳定且唯一。"""
from __future__ import annotations

from fastapi.routing import APIRoute

from src.app import app


def _api_routes() -> list[APIRoute]:
    return [r for r in app.routes if isinstance(r, APIRoute)]


def test_all_routes_have_operation_id():
    """operation_id 缺省=函数名 (app._use_route_names_as_operation_ids);
    同函数多路径的路由必须在装饰器显式给 id — 总之不允许为空。"""
    for route in _api_routes():
        assert route.operation_id, f"{route.path} 缺 operation_id"


def test_all_operation_ids_unique():
    seen: dict[str, str] = {}
    for route in _api_routes():
        op = route.operation_id or route.name
        assert op not in seen, (
            f"operation_id {op!r} 重复: {seen[op]} 与 {route.path} — 改函数名保证唯一"
        )
        seen[op] = route.path


def test_openapi_schema_generates():
    schema = app.openapi()
    assert len(schema["paths"]) >= 37


def test_risk_state_endpoint(engine_and_client=None):
    """GET /api/risk/state 登录可见 + 匿名拒绝 (B2)。"""
    import os

    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from src.controllers.dependencies import get_current_user
    from src.db.session import get_db
    from src.models import Base

    eng = create_engine(os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(eng)

    def _override():
        s = Session(eng)
        try:
            yield s
        finally:
            s.close()

    from types import SimpleNamespace

    app.dependency_overrides[get_db] = _override
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, username="u", role="user", status="active",
    )
    try:
        cli = TestClient(app)
        r = cli.get("/api/risk/state")
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["data"]["state"] in {"OK", "WARN", "HALTED"}
        assert set(body["data"]) == {"state", "day_loss_pct", "positions_pct", "regime"}
    finally:
        app.dependency_overrides.clear()

    r2 = TestClient(app).get("/api/risk/state")
    assert r2.json()["code"] == "400003"


def test_core_read_models_present_in_openapi_components():
    """B1: 核心端点 data 有具体模型, 前端生成的不再是 unknown。"""
    schema = app.openapi()
    components = set(schema.get("components", {}).get("schemas", {}).keys())
    required = {
        "PositionRead", "TradeRead", "AccountSnapshotRead", "DecisionRead",
        "DecisionDetailOut", "RiskEventRead", "RiskStateOut",
        "KlineRead", "TickerOut", "MarketSymbolRead",
        "PrecheckOut", "OrderPlacedOut", "LoginOut", "UserRead", "RolesOut",
    }
    missing = required - components
    assert not missing, f"OpenAPI components 缺模型: {missing}"
