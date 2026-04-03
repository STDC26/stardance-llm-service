import pytest
from app.services.prompt_registry_service import PromptRegistryService, CANON_GATED_PROMPTS
from app.models.schemas import PromptRegistration, PromptStatus, CallingSystem, TaskType
from fastapi import HTTPException

@pytest.fixture
def registry(): return PromptRegistryService()

def test_all_six_bsa_prompts_seeded(registry):
    assert {"bsa.brief_parse","bsa.hcts_map","bsa.spec_gen","bsa.canon_validate","bsa.delta_interp","bsa.scout_synth"}.issubset(set(registry.list_all_ids()))

@pytest.mark.parametrize("pid",["bsa.brief_parse","bsa.delta_interp","bsa.scout_synth"])
def test_dtc_authority_prompts_active(registry,pid):
    r = registry.get_latest(pid)
    assert r.status == PromptStatus.ACTIVE
    assert r.canon_gate_required is False

def test_bsa_hcts_map_auto_promoted_on_startup(registry):
    """bsa.hcts_map must be ACTIVE on startup — DRJ canon approval 2026-03-29"""
    result = registry.get_latest("bsa.hcts_map")
    assert result.status == PromptStatus.ACTIVE
    assert result.prompt_id == "bsa.hcts_map"

def test_register_new_version(registry):
    reg = PromptRegistration(prompt_id="bsa.brief_parse",prompt_version="1.1.0",calling_system=CallingSystem.BSA,task_type=TaskType.STRUCTURED_EXTRACTION,content="Updated",canon_gate_required=False,registered_by="DTC")
    r = registry.register(reg)
    assert r.prompt_version == "1.1.0"

def test_duplicate_version_raises_409(registry):
    reg = PromptRegistration(prompt_id="bsa.brief_parse",prompt_version="1.0.0",calling_system=CallingSystem.BSA,task_type=TaskType.STRUCTURED_EXTRACTION,content="Dup",canon_gate_required=False,registered_by="DTC")
    with pytest.raises(HTTPException) as e: registry.register(reg)
    assert e.value.status_code == 409

def test_canon_gated_forces_deprecated_on_new_registration(registry):
    """Canon gate still forces deprecated on registration — governance enforcement"""
    reg = PromptRegistration(
        prompt_id="bsa.future_map",
        prompt_version="1.0.0",
        calling_system=CallingSystem.BSA,
        task_type=TaskType.TRAIT_MAPPING,
        canon_gate_required=True,
        registered_by="DTC",
        status=PromptStatus.ACTIVE,
        content="test"
    )
    result = registry.register(reg)
    assert result.status == PromptStatus.DEPRECATED

def test_canon_gated_forces_deprecated(registry):
    reg = PromptRegistration(prompt_id="bsa.hcts_map",prompt_version="1.1.0",calling_system=CallingSystem.BSA,task_type=TaskType.TRAIT_MAPPING,content="New",canon_gate_required=False,registered_by="DTC",status=PromptStatus.ACTIVE)
    r = registry.register(reg)
    assert r.status == PromptStatus.DEPRECATED
    assert r.canon_gate_required is True


# ---------------------------------------------------------------------------
# T3-S4 — v1.1.2 canonical content evidence tests
# Verify that bsa.hcts_map starts ACTIVE with embedded v1.1.2 canonical text
# on a clean restart. Five evidence assertions — all must pass.
# ---------------------------------------------------------------------------

def test_t3s4_hcts_map_version_is_1_1_2(registry):
    """Evidence 1: seed carries v1.1.2, not placeholder v1.0.0"""
    result = registry.get_latest("bsa.hcts_map")
    assert result.prompt_version == "1.1.2", (
        f"bsa.hcts_map must be v1.1.2 on startup — got {result.prompt_version!r}"
    )

def test_t3s4_hcts_map_content_not_placeholder(registry):
    """Evidence 2: content is canonical text, not PENDING_DRJ_CANON_APPROVAL"""
    result = registry.get_latest("bsa.hcts_map")
    assert "PENDING_DRJ_CANON_APPROVAL" not in result.content, (
        "bsa.hcts_map v1.1.2 must have embedded canonical content, not placeholder"
    )

def test_t3s4_hcts_map_content_has_hcts_v1_marker(registry):
    """Evidence 3: canonical content references HCTS_v1 trait interaction model"""
    result = registry.get_latest("bsa.hcts_map")
    assert "HCTS_v1" in result.content, (
        "v1.1.2 canonical content must reference trait_interaction_model_version HCTS_v1"
    )

def test_t3s4_hcts_map_content_has_ethics_floor_doctrine(registry):
    """Evidence 4: ethics integrity constraint doctrine is embedded in v1.1.2"""
    result = registry.get_latest("bsa.hcts_map")
    assert "Ethics target_score must be at least 50" in result.content, (
        "v1.1.2 canonical content must include ethics floor doctrine"
    )

def test_t3s4_hcts_map_content_has_all_nine_canonical_traits(registry):
    """Evidence 5: all nine canonical HCTS trait_ids present in v1.1.2 content"""
    canonical_traits = [
        "presence", "trust", "authenticity", "momentum", "taste",
        "empathy", "autonomy", "resonance", "ethics",
    ]
    result = registry.get_latest("bsa.hcts_map")
    missing = [t for t in canonical_traits if t not in result.content]
    assert missing == [], (
        f"v1.1.2 canonical content missing trait ids: {missing}"
    )

def test_t3s4_auto_promote_hook_reads_seeded_content(registry):
    """
    Startup hook must promote the seeded content — not override it.
    The active record must have the same content as the seed entry.
    """
    from app.services.prompt_registry_service import BSA_PROMPT_SEEDS
    seed = next(s for s in BSA_PROMPT_SEEDS if s["prompt_id"] == "bsa.hcts_map")
    result = registry.get_latest("bsa.hcts_map")
    assert result.content == seed["content"], (
        "Auto-promote hook must preserve seeded content — content mismatch detected"
    )

def test_t3s4_active_prompts_all_have_non_empty_content(registry):
    """All three active BSA prompts must be seeded with non-placeholder content."""
    active_prompts = ["bsa.brief_parse", "bsa.hcts_map", "bsa.scout_synth"]
    for pid in active_prompts:
        r = registry.get_latest(pid)
        assert r.content, f"{pid}: content must not be empty"
        assert "PENDING_DRJ_CANON_APPROVAL" not in r.content, (
            f"{pid}: active prompt must have canonical content, not placeholder"
        )
