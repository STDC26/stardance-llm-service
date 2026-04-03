from app.models.schemas import (PromptRegistration, PromptRecord, PromptStatus, CallingSystem, TaskType)
from fastapi import HTTPException
from collections import defaultdict
from typing import Optional

CANON_GATED_PROMPTS = {"bsa.hcts_map"}

BSA_PROMPT_SEEDS: list[dict] = [
    {"prompt_id": "bsa.brief_parse", "prompt_version": "1.0.0", "calling_system": CallingSystem.BSA, "task_type": TaskType.STRUCTURED_EXTRACTION, "content": "Extract structured fields from the following campaign brief. Return a JSON object with keys: campaign_goal, brand_domain, asset_type, channel_spec, duration_constraint, audience_notes, raw_brief. If a field is not present, return null.\n\nBrief:{brief_text}", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
    {"prompt_id": "bsa.hcts_map", "prompt_version": "1.1.2", "calling_system": CallingSystem.BSA, "task_type": TaskType.TRAIT_MAPPING, "content": "You are the Stardance HCTS Mapping Agent. Your task is to map a campaign brief to HCTS conviction targets across exactly nine canonical traits.\n\nYou will receive:\n- brief_text: the raw campaign brief\n- brand_domain: the brand category or domain (e.g. beauty, saas, financial_services)\n- scout_context: SCOUT market intelligence summary (may be empty string)\n\nThe nine canonical HCTS traits are fixed and immutable. You must score all nine. No others:\n  1. Presence      — visual command and immediate impact\n  2. Trust         — credibility, claim integrity, authority\n  3. Authenticity  — genuine, real, not performative\n  4. Momentum      — forward energy, pace, drive\n  5. Taste         — aesthetic precision, restraint, quality\n  6. Empathy       — human truth, emotional connection\n  7. Autonomy      — viewer empowerment, reduced pressure, clarity of choice\n  8. Resonance     — cultural connection, memorability\n  9. Ethics        — integrity, no manipulation, no false claims\n\nDomain signal guidance — use brand_domain to shape trait conviction targets:\n- beauty / fashion / lifestyle: elevate Taste, Empathy, Presence. These domains lead with aesthetic and emotional connection. Trust and Autonomy are secondary.\n- saas / b2b / fintech / financial_services: elevate Trust, Autonomy. These domains lead with credibility, clarity, and user empowerment. Taste and Empathy are secondary.\n- consumer / fmcg / food: elevate Empathy, Authenticity, Resonance. Human truth and cultural connection lead.\n- health / wellness / medical: elevate Trust, Ethics, Empathy. Credibility and integrity are primary.\n- entertainment / gaming / media: elevate Presence, Momentum, Resonance. Impact and energy lead.\n- When brand_domain does not match a category above, use brief_text signals to determine dominant traits.\n\nScoring scale: 0 to 100 (integers only). Higher scores indicate stronger conviction target for that trait.\n\nReturn this exact JSON structure:\n{\n  \"traits\": [\n    {\"trait_id\": \"presence\", \"trait_name\": \"Presence\", \"target_score\": 0, \"conviction_rationale\": \"...\"},\n    {\"trait_id\": \"trust\", \"trait_name\": \"Trust\", \"target_score\": 0, \"conviction_rationale\": \"...\"},\n    {\"trait_id\": \"authenticity\", \"trait_name\": \"Authenticity\", \"target_score\": 0, \"conviction_rationale\": \"...\"},\n    {\"trait_id\": \"momentum\", \"trait_name\": \"Momentum\", \"target_score\": 0, \"conviction_rationale\": \"...\"},\n    {\"trait_id\": \"taste\", \"trait_name\": \"Taste\", \"target_score\": 0, \"conviction_rationale\": \"...\"},\n    {\"trait_id\": \"empathy\", \"trait_name\": \"Empathy\", \"target_score\": 0, \"conviction_rationale\": \"...\"},\n    {\"trait_id\": \"autonomy\", \"trait_name\": \"Autonomy\", \"target_score\": 0, \"conviction_rationale\": \"...\"},\n    {\"trait_id\": \"resonance\", \"trait_name\": \"Resonance\", \"target_score\": 0, \"conviction_rationale\": \"...\"},\n    {\"trait_id\": \"ethics\", \"trait_name\": \"Ethics\", \"target_score\": 0, \"conviction_rationale\": \"...\"}\n  ],\n  \"overall_conviction_score\": 0,\n  \"trait_interaction_model_version\": \"HCTS_v1\",\n  \"mapping_rationale\": \"One sentence describing the dominant trait direction for this brief\"\n}\n\nArithmetic:\n- overall_conviction_score = sum of all nine target_scores divided by 9, rounded to nearest integer\n- No hidden weights. Equal weight per trait.\n\nGoverning trait doctrine:\n- Ethics is not a performance dimension — it is an integrity constraint\n- Ethics target_score must be at least 50 at all times\n- If a brief appears to require ethics below 50, set ethics to 50 and note the floor in conviction_rationale\n\nRules:\n- target_score values must be integers between 0 and 100\n- All nine traits must be present — no additions, no omissions\n- trait_id values must exactly match: presence, trust, authenticity, momentum, taste, empathy, autonomy, resonance, ethics\n- trait_name values must exactly match: Presence, Trust, Authenticity, Momentum, Taste, Empathy, Autonomy, Resonance, Ethics\n- Do not use synonyms\n- trait_interaction_model_version must always be HCTS_v1\n- conviction_rationale must be specific to this brief\n- Return valid JSON only. No markdown. No preamble.", "canon_gate_required": True, "registered_by": "DTC", "status": PromptStatus.DEPRECATED},
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
        # Auto-promote canon-approved prompts on startup
        self._auto_promote_approved()

    def _auto_promote_approved(self):
        """
        Auto-promote prompts that have received DRJ canon approval.
        Called on registry startup after seeding.
        Canon approvals are recorded here as the authoritative approval log.
        """
        CANON_APPROVED = {
            "bsa.hcts_map": {
                "version": "1.1.2",
                "approved_by": "DRJ",
                "approved_date": "2026-03-29",
                "approval_ref": "BSA Canon Review Pack v1.1 — Gate 4 session — v1.1.2 validated T3-S3 2026-04-02"
            },
        }
        for prompt_id, approval in CANON_APPROVED.items():
            versions = self._store.get(prompt_id, [])
            for v in versions:
                if v.prompt_version == approval["version"]:
                    v.status = PromptStatus.ACTIVE
                    break

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
        if registration.prompt_id in CANON_GATED_PROMPTS or registration.canon_gate_required:
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

