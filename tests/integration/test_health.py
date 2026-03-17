import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from app.main import app

@pytest.mark.asyncio
async def test_health_returns_200():
    with patch("app.routers.health._check_anthropic",new=AsyncMock(return_value=True)), patch("app.routers.health._check_cache",new=AsyncMock(return_value=True)):
        async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as c:
            r = await c.get("/v1/llm/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_health_degraded():
    with patch("app.routers.health._check_anthropic",new=AsyncMock(return_value=False)), patch("app.routers.health._check_cache",new=AsyncMock(return_value=True)):
        async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as c:
            r = await c.get("/v1/llm/health")
    assert r.json()["status"] == "degraded"
