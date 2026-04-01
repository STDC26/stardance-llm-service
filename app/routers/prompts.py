from fastapi import APIRouter, Depends
from app.models.schemas import PromptRegistration, PromptRecord, PromptVersionList
from app.services.prompt_registry_service import PromptRegistryService, get_prompt_registry

router = APIRouter()

@router.get("/prompts/{prompt_id}", response_model=PromptRecord, tags=["Prompts"])
async def get_prompt(prompt_id: str, registry: PromptRegistryService = Depends(get_prompt_registry)):
    return registry.get_latest(prompt_id)

@router.get("/prompts/{prompt_id}/versions", response_model=PromptVersionList, tags=["Prompts"])
async def list_prompt_versions(prompt_id: str, registry: PromptRegistryService = Depends(get_prompt_registry)):
    return PromptVersionList(prompt_id=prompt_id, versions=registry.list_versions(prompt_id))

@router.get("/prompts/{prompt_id}/versions/{version}", response_model=PromptRecord, tags=["Prompts"])
async def get_prompt_version(prompt_id: str, version: str, registry: PromptRegistryService = Depends(get_prompt_registry)):
    return registry.get_version(prompt_id, version)

@router.post("/prompts", response_model=PromptRecord, status_code=201, tags=["Prompts"])
async def register_prompt(registration: PromptRegistration, registry: PromptRegistryService = Depends(get_prompt_registry)):
    return registry.register(registration)

@router.post("/prompts/{prompt_id}/promote/{version}", tags=["Prompts"])
async def promote_prompt(prompt_id: str, version: str, registry: PromptRegistryService = Depends(get_prompt_registry)):
    """DRJ-authorized promotion of a canon-gated prompt to ACTIVE."""
    return registry.promote(prompt_id, version)
