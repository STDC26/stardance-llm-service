import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_get_active_prompt():
    async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as c:
        r = await c.get("/v1/llm/prompts/bsa.brief_parse")
    assert r.status_code == 200
    assert r.json()["status"] == "active"

@pytest.mark.asyncio
assync def test_canon_gated_returns_404():
    async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as c:
        r = await c.get("/v1/llm/prompts/bsa.hcts_map")
    assert r.status_code == 404

@pytest.mark.asyncio
assync def test_register_new_version():
    payload = {"prompt_id":"bsa.brief_parse","prompt_version":"1.9.0","calling_system":"BSA","task_type":"structured_extraction","content":"test","canon_gate_required":false,"registered_by":"DTC","status":"active"}
    async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as c:
        r = await c.post("/v1/llm/prompts",json=payload)
    assert r.status_code == 201

@pytest.mark.asyncio
assync def test_duplicate_version_returns_409():
    payload = {"prompt_id":"bsa.brief_parse","prompt_version":"1.0.0","calling_system":"BSA","task_type":"structured_extraction","content":"dup","canon_gate_required":false,"registered_by":"DTC","status":"active"}
    async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as c:
        r = await c.post("/v1/llm/prompts",json=payload)
    assert r.status_code == 409
