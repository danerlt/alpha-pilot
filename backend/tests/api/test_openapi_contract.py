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
