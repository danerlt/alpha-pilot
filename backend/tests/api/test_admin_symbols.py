import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.shared.db import get_db
from src.shared.models.audit_log import AuditLog
from src.shared.models.base import Base
from src.shared.models.symbol_config import SymbolConfig


@pytest.fixture
def admin_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(engine, tables=[SymbolConfig.__table__, AuditLog.__table__])
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.mark.asyncio
async def test_admin_can_create_and_list_symbols(admin_db):
    from src.api import router as router_module

    def override_db():
        yield admin_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[router_module.require_admin] = lambda: type("Admin", (), {"id": 1})()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/admin/symbols",
                json={"symbol": "BTCUSDT", "base_asset": "BTC", "quote_asset": "USDT", "timeframe": "15m"},
            )
            assert create_resp.status_code == 200

            list_resp = await client.get("/api/admin/symbols")
            assert list_resp.status_code == 200
            data = list_resp.json()
            assert len(data) == 1
            assert data[0]["symbol"] == "BTCUSDT"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_can_update_symbol(admin_db):
    from src.api import router as router_module

    symbol = SymbolConfig(symbol="ETHUSDT", base_asset="ETH", quote_asset="USDT", timeframe="15m")
    admin_db.add(symbol)
    admin_db.commit()
    admin_db.refresh(symbol)

    def override_db():
        yield admin_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[router_module.require_admin] = lambda: type("Admin", (), {"id": 1})()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.patch(
                f"/api/admin/symbols/{symbol.id}",
                json={"enabled": False, "timeframe": "1h", "notes": "disabled for review"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["enabled"] is False
            assert data["timeframe"] == "1h"
    finally:
        app.dependency_overrides.clear()
