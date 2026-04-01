from app.models.schemas import (PromptRegistration, PromptRecord, PromptStatus, CallingSystem, TaskType)
from fastapi import HTTPException
from collections import defaultdict
from typing import Optional

CANON_GATED_PROMPTS = {"bsa.hcts_map"}

BSA_PROMPT_SEEDS: list[dict] = [
    {"prompt_id": "bsa.brief_parse", "prompt_version": "1.0.0", "calling_system": CallingSystem.BSA, "task_type": TaskType.STRUCTURED_EXTRACTION, "content": "Extract structured fields from the following campaign brief. Return a JSON object with keys: campaign_goal, brand_domain, asset_type, channel_spec, duration_constraint, audience_notes, raw_brief. If a field is not present, return null.\n\nBrief:{brief_text}", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
    {"prompt_id": "bsa.hcts_map", "prompt_version": "1.0.0", "calling_system": CallingSystem.BSA, "task_type": TaskType.TRAIT_MAPPING, "content": "PENDING_DRJ_CANON_APPROVAL", "canon_gate_required": True, "registered_by": "DTC", "status": PromptStatus.DEPRECATED},
    {"prompt_id": "bsa.spec_gen", "prompt_version": "1.0.0", "calling_system": CallingSystem.BSA, "task_type": TaskType.SPECIFICATION_GENERATION, "content": "PENDING_DRJ_CANON_APPROVAL", "canon_gate_required": True, "registered_by": "DTC", "status": PromptStatus.DEPRECATED},
    {"prompt_id": "bsa.canon_validate", "prompt_version": "1.0.0", "calling_system": CallingSystem.BSA, "task_type": TaskType.VALIDATION, "content": "PENDING_DRJ_CANON_APPROVAL", "canon_gate_required": True, "registered_by": "DTC", "status": PromptStatus.DEPRECATED},
    {"prompt_id": "bsa.delta_interp", "prompt_version": "1.0.0", "calling_system": CallingSystem.BSA, "task_type": TaskType.DELTA_INTERPRETATION, "content": "The following HCTS trait delta could not be resolved by the math layer. Provide a brief interpretation of the likely gap. Do not assign numeric scores.\n\nContext:\n{delta_context}", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
    {"prompt_id": "bsa.scout_synth", "prompt_version": "1.0.0", "calling_system": CallingSystem.BSA, "task_type": TaskType.SCOUT_SYNTHESIS, "content": "Synthesise SCOUT market signals into a brief context summary. Return JSON with keys: market_context, competitor_signals, trend_signals, relevance_score.\n\nBrief:\n{brief_context}\n\nSCOUT:\n{scout_signals}", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
]


class PromptRegistryService:
    def __init__(self):
        self._store = defaultdict(list)
        for seed in BSA_PROMPT_SEEDS:
            self._store[seed["prompt_id"]].append(PromptRecord(**seed))

    def get_latest(self, prompt_id):
        versions = self._store.get(prompt_id)
        if not versions: raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_id}")
        active = [v for v in versions if v.status == PromptStatus.ACTIVE]
        if not active: raise HTTPException(status_code=404, detail=f"No active version for prompt: {prompt_id}. Check canon gate status.")
        return active[-1]

    def get_version(self, prompt_id, version):
        versions = self._store.get(prompt_id)
        if not versions: raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_id}")
        for v in versions:
            if v.prompt_version == version: return v
        raise HTTPException(status_code=404, detail=f"Version {version} not found for: {prompt_id}")

    def list_versions(self, prompt_id):
        versions = self._store.get(prompt_id)
        if not versions: raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_id}")
        return versions

    def register(self, registration):
        for v in self._store.get(registration.prompt_id, []):
            if v.prompt_version == registration.prompt_version: raise HTTPException(status_code=409, detail=f"Version {registration.prompt_version} already exists for {registration.prompt_id}.")
        if registration.prompt_id in CANON_GATED_PROMPTS:
            registration = registration.model_copy(update={"status": PromptStatus.DEPRECATED, "canon_gate_required": True})
        record = PromptRecord(**registration.model_dump())
        self._store[registration.prompt_id].append(record)
        return record

    def resolve_for_call(self, prompt_id, version=None):
        return self.get_version(prompt_id, version) if version else self.get_latest(prompt_id)

    def list_all_ids(self):
        return list(self._store.keys())


    def promote(self, prompt_id: str, version: str) -> dict:
        """DRJ-authorized promotion — bypasses canon gate for approved prompts."""
        versions = self._store.get(prompt_id, [])
        for v in versions:
            if v.prompt_version == version:
                v.status = PromptStatus.ACTIVE
                return {"promoted": True, "prompt_id": prompt_id, "version": version, "status": "active"}
        return {"promoted": False, "detail": f"Version {version} not found for {prompt_id}"}


_registry = None


def get_prompt_registry():
    global _registry
    if _registry is None:
        _registry = PromptRegistryService()
    return _registry

