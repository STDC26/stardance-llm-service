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

@pytest.mark.parametrize("pid",["bsa.hcts_map"])
def test_canon_gated_deprecated(registry,pid):
    assert pid in CANON_GATED_PROMPTS
    with pytest.raises(HTTPException) as e: registry.get_latest(pid)
    assert e.value.status_code == 404

def test_register_new_version(registry):
    reg = PromptRegistration(prompt_id="bsa.brief_parse",prompt_version="1.1.0",calling_system=CallingSystem.BSA,task_type=TaskType.STRUCTURED_EXTRACTION,content="Updated",canon_gate_required=False,registered_by="DTC")
    r = registry.register(reg)
    assert r.prompt_version == "1.1.0"

def test_duplicate_version_raises_409(registry):
    reg = PromptRegistration(prompt_id="bsa.brief_parse",prompt_version="1.0.0",calling_system=CallingSystem.BSA,task_type=TaskType.STRUCTURED_EXTRACTION,content="Dup",canon_gate_required=False,registered_by="DTC")
    with pytest.raises(HTTPException) as e: registry.register(reg)
    assert e.value.status_code == 409

def test_canon_gated_forces_deprecated(registry):
    reg = PromptRegistration(prompt_id="bsa.hcts_map",prompt_version="1.1.0",calling_system=CallingSystem.BSA,task_type=TaskType.TRAIT_MAPPING,content="New",canon_gate_required=False,registered_by="DTC",status=PromptStatus.ACTIVE)
    r = registry.register(reg)
    assert r.status == PromptStatus.DEPRECATED
    assert r.canon_gate_required is True
