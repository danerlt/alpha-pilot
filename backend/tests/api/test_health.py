import pytest
from httpx import AsyncClient, ASGITransport
from src.app.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "trading_mode" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_root_redirect():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code in (200, 307, 308)
