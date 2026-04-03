import pytest
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_get_active_prompt():
    async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as c:
        r = await c.get("/v1/llm/prompts/bsa.brief_parse")
    assert r.status_code == 200
    assert r.json()["status"] == "active"

def test_canon_gated_auto_promoted_returns_200(client):
    """bsa.hcts_map is canon-gated but auto-promoted on startup — must return 200"""
    r = client.get("/v1/llm/prompts/bsa.hcts_map")
    assert r.status_code == 200
    assert r.json()["status"] == "active"

def test_canon_gated_unapproved_returns_404(client):
    """Canon-gated prompts without DRJ approval must return 404"""
    r = client.get("/v1/llm/prompts/bsa.future_map")
    assert r.status_code == 404

@pytest.mark.asyncio
async def test_register_new_version():
    payload = {"prompt_id":"bsa.brief_parse","prompt_version":"1.9.0","calling_system":"BSA","task_type":"structured_extraction","content":"test","canon_gate_required":False,"registered_by":"DTC","status":"active"}
    async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as c:
        r = await c.post("/v1/llm/prompts",json=payload)
    assert r.status_code == 201

@pytest.mark.asyncio
async def test_duplicate_version_returns_409():
    payload = {"prompt_id":"bsa.brief_parse","prompt_version":"1.0.0","calling_system":"BSA","task_type":"structured_extraction","content":"dup","canon_gate_required":False,"registered_by":"DTC","status":"active"}
    async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as c:
        r = await c.post("/v1/llm/prompts",json=payload)
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# T3-S4 — Integration: clean restart produces active bsa.hcts_map v1.1.2
# ---------------------------------------------------------------------------

def test_t3s4_hcts_map_endpoint_returns_v1_1_2(client):
    """Clean restart: /v1/llm/prompts/bsa.hcts_map returns version 1.1.2"""
    r = client.get("/v1/llm/prompts/bsa.hcts_map")
    assert r.status_code == 200
    body = r.json()
    assert body["prompt_version"] == "1.1.2", (
        f"Expected v1.1.2 from endpoint — got {body.get('prompt_version')!r}"
    )

def test_t3s4_hcts_map_endpoint_content_is_canonical(client):
    """Clean restart: endpoint content is canonical text, not placeholder"""
    r = client.get("/v1/llm/prompts/bsa.hcts_map")
    assert r.status_code == 200
    body = r.json()
    content = body.get("content", "")
    assert "PENDING_DRJ_CANON_APPROVAL" not in content
    assert "HCTS_v1" in content
    assert "Ethics target_score must be at least 50" in content

def test_t3s4_hcts_map_endpoint_no_manual_promote_required(client):
    """
    bsa.hcts_map must be active on a clean app startup with no manual steps.
    The auto-promote hook fires on PromptRegistryService.__init__() — the
    endpoint must return 200/active without any prior promote call.
    """
    r = client.get("/v1/llm/prompts/bsa.hcts_map")
    assert r.status_code == 200
    assert r.json()["status"] == "active"
