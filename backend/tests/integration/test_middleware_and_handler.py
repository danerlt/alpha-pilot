"""验证 RequestLogging / ErrorLogging 中间件 + 全局异常 handler 协作。"""
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.common.exception.errors import RiskRejectedException
from src.common.exception.exception_handler import register_exception_handlers
from src.middleware.error_logging_middleware import ErrorLoggingMiddleware
from src.middleware.request_logging_middleware import RequestLoggingMiddleware


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.add_middleware(ErrorLoggingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/risk")
    def _r():
        raise RiskRejectedException("日内亏损超阈")

    @app.get("/unknown")
    def _u():
        raise RuntimeError("boom")

    @app.get("/ping")
    def _ping():
        return {"pong": True}

    return app


def test_request_logging_middleware_logs_path(caplog):
    caplog.set_level(logging.INFO, logger="middleware.request")
    client = TestClient(_build_app())
    resp = client.get("/ping")
    assert resp.status_code == 200
    matching = [r for r in caplog.records if "/ping" in r.getMessage()]
    assert len(matching) >= 1


def test_app_base_exception_returns_200_with_success_false():
    client = TestClient(_build_app())
    resp = client.get("/risk")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert body["code"] == "600002"
    assert body["message"] == "日内亏损超阈"


def test_unhandled_exception_returns_200_with_sys_error():
    client = TestClient(_build_app(), raise_server_exceptions=False)
    resp = client.get("/unknown")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert body["code"] == "500001"
