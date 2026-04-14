from app.models.schemas import (PromptRegistration, PromptRecord, PromptStatus, CallingSystem, TaskType)
from fastapi import HTTPException
from collections import defaultdict
from typing import Optional

CANON_GATED_PROMPTS = {"bsa.hcts_map"}

CIF_PROMPT_SEEDS: list[dict] = [
    {"prompt_id": "cif.copilot", "prompt_version": "1.0.0", "calling_system": CallingSystem.CIF, "task_type": TaskType.SPECIFICATION_GENERATION, "content": "{prompt}", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
    {"prompt_id": "cif.qds-draft", "prompt_version": "1.0.0", "calling_system": CallingSystem.CIF, "task_type": TaskType.SPECIFICATION_GENERATION, "content": "You are a qualification flow designer. Generate a 3-step diagnostic quiz for the sector described. Return ONLY a JSON object with: steps (array of 3 objects each with title, prompt, options array of 4 objects each with label, value, score_weight 0-1), outcomes (array of 3 objects with label, qualification_status, score_band_min, score_band_max, message).\n\nSector: {sector}\nProduct: {product_name}\nGoal: {qualification_goal}", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
    {"prompt_id": "cif.signal-insight", "prompt_version": "1.0.0", "calling_system": CallingSystem.CIF, "task_type": TaskType.SPECIFICATION_GENERATION, "content": "You are a marketing analyst. Interpret the signal event data below and provide a 2-3 sentence insight about user behaviour patterns. Focus on drop-off points, conversion friction, and engagement quality. Be specific and actionable.\n\nAsset: {asset_name}\nTotal events: {total_events}\nEvent breakdown: {event_breakdown}\nTime period: {time_period}", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
    {"prompt_id": "cif.asset-insight", "prompt_version": "1.0.0", "calling_system": CallingSystem.CIF, "task_type": TaskType.SPECIFICATION_GENERATION, "content": "You are a conversion optimisation analyst. Analyse the asset performance data below and provide a 2-3 sentence insight covering: what is working, what is not, and one specific recommended action. Be concrete.\n\nAsset: {asset_name} ({asset_type})\nStatus: {asset_status}\nVersions: {version_count}\nDeployed version: {deployed_version}\nTotal events: {total_events}\nPerformance summary: {performance_summary}", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
    {"prompt_id": "cif.experiment-insight", "prompt_version": "1.0.0", "calling_system": CallingSystem.CIF, "task_type": TaskType.SPECIFICATION_GENERATION, "content": "You are an A/B testing analyst. Interpret the experiment results below and provide a clear 2-3 sentence conclusion: which variant won, by how much, and whether the result is statistically meaningful enough to act on.\n\nExperiment: {experiment_name}\nHypothesis: {hypothesis}\nPrimary metric: {primary_metric}\nVariant data: {variant_data}", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
    {"prompt_id": "cif.variant-generator", "prompt_version": "1.0.0", "calling_system": CallingSystem.CIF, "task_type": TaskType.SPECIFICATION_GENERATION, "content": "You are a conversion copywriter. Generate {variant_count} alternative versions of the component content below. Each variant should test a meaningfully different angle (urgency vs benefit vs social proof). Return ONLY a JSON array of objects matching the original component structure.\n\nComponent type: {component_type}\nOriginal content: {original_content}\nContext: {brand_context}", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
    {"prompt_id": "cif.experiment-recommend", "prompt_version": "1.0.0", "calling_system": CallingSystem.CIF, "task_type": TaskType.SPECIFICATION_GENERATION, "content": "You are a growth strategist. Based on the asset performance data below, recommend 2-3 specific A/B experiments that would most likely improve conversion rate. For each specify: what to test, the hypothesis, and the primary metric. Return ONLY a JSON array of experiment recommendation objects.\n\nAsset: {asset_name}\nPerformance: {performance_summary}\nCurrent components: {component_summary}", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
    # CQX stage directive prompts — conviction sequencing layer
    {"prompt_id": "cif.copilot.context", "prompt_version": "1.0.0", "calling_system": CallingSystem.CIF, "task_type": TaskType.SPECIFICATION_GENERATION, "content": "You are writing the Context stage of a conviction surface. Your job is to make clear why this matters — not to sell. The audience is arriving with no prior context. HCTS profile: {hcts_profile}. Intensity: {cqx_intensity}. Write one headline and one subheadline. No claims. No urgency. Just relevance. The user must understand why this surface exists for them.", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
    {"prompt_id": "cif.copilot.outcome", "prompt_version": "1.0.0", "calling_system": CallingSystem.CIF, "task_type": TaskType.SPECIFICATION_GENERATION, "content": "You are writing the Outcome stage of a conviction surface. Show what is possible — the result the user could achieve. Be specific and evidence-grounded. No superlatives. HCTS authenticity target: {authenticity_score}. Intensity: {cqx_intensity}. Write 3 trust points — short, factual, scannable. Each must be a real claim, not a feature list.", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
    {"prompt_id": "cif.copilot.direction", "prompt_version": "1.0.0", "calling_system": CallingSystem.CIF, "task_type": TaskType.SPECIFICATION_GENERATION, "content": "You are writing the Direction stage of a conviction surface. The user understands context and outcome. Show them the next step — not the sale. HCTS autonomy target: {autonomy_score}. Intensity: {cqx_intensity}. The user must feel they are choosing, not being pushed. Write one direction prompt: one sentence that guides without commanding.", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
    {"prompt_id": "cif.copilot.conviction", "prompt_version": "1.0.0", "calling_system": CallingSystem.CIF, "task_type": TaskType.SPECIFICATION_GENERATION, "content": "You are writing the Conviction stage of a conviction surface. This is where felt understanding forms — not explained understanding. Use social proof, evidence, or authority matched to HCTS profile: {hcts_profile}. Intensity: {cqx_intensity}. Write one social proof quote and one supporting trust signal. The user must feel the result, not read about it. Delight is the ignition point of conviction.", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
    {"prompt_id": "cif.copilot.action", "prompt_version": "1.0.0", "calling_system": CallingSystem.CIF, "task_type": TaskType.SPECIFICATION_GENERATION, "content": "You are writing the Action stage of a conviction surface. conviction_expectation is {conviction_expectation}. Rules: if actionable — one directive CTA label, no optionality, high commitment language. If directional — soften commitment, preserve user agency. If low — write a discovery CTA, do not close. HCTS autonomy: {autonomy_score}. The user is the author of this decision.", "canon_gate_required": False, "registered_by": "DTC", "status": PromptStatus.ACTIVE},
]

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
        for seed in CIF_PROMPT_SEEDS + BSA_PROMPT_SEEDS:
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
        return self.get_version(prompt_id, version) if (version and version != "latest") else self.get_latest(prompt_id)

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

