from pydantic import BaseModel, ConfigDict, Field, UUID4, field_validator
from typing import Any, Optional
from enum import Enum
from datetime import datetime, timezone
import uuid

def _utcnow():
    return datetime.now(timezone.utc)

class CallingSystem(str, Enum):
    BSA = "BSA"
    BASE = "BASE"
    CIF = "CIF"
    CIDE = "CIDE"
    SCOUT = "SCOUT"
    EDGE = "EDGE"
    CORTEX = "CORTEX"

class TaskType(str, Enum):
    STRUCTURED_EXTRACTION = "structured_extraction"
    TRAIT_MAPPING = "trait_mapping"
    SPECIFICATION_GENERATION = "specification_generation"
    VALIDATION = "validation"
    DELTA_INTERPRETATION = "delta_interpretation"
    SCOUT_SYNTHESIS = "scout_synthesis"
    VISION_ASSESSMENT = "vision_assessment"
    OUTPUT_VALIDATION = "output_validation"
    ANOMALY_INTERPRETATION = "anomaly_interpretation"

class PromptStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"

class LLMCallRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    call_id: UUID4 = Field(default_factory=uuid.uuid4)
    calling_system: CallingSystem
    task_type: TaskType
    payload: dict
    prompt_id: str
    prompt_version: Optional[str] = None
    model_hint: Optional[str] = None
    high_stakes_flag: bool = False
    cache_eligible: bool = True
    cache_ttl_seconds: int = Field(default=86400, ge=0)
    schema_version: str = "1.0.0"

class LLMCallResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    call_id: UUID4
    content: str
    model_used: str
    model_version: str
    prompt_id: str
    prompt_version: str
    fallback_chain: list = []
    cache_hit: bool = False
    tokens_in: int
    tokens_out: int
    cost_usd: float
    latency_ms: int
    calling_system: CallingSystem
    task_type: TaskType
    responded_at: datetime = Field(default_factory=_utcnow)

class PromptRegistration(BaseModel):
    prompt_id: str
    prompt_version: str
    calling_system: CallingSystem
    task_type: TaskType
    content: str
    canon_gate_required: bool = False
    registered_by: str
    status: PromptStatus = PromptStatus.ACTIVE
    @field_validator("prompt_id")
    @classmethod
    def validate_prompt_id(cls, v):
        if "." not in v:
            raise ValueError("prompt_id must follow system.name format")
        return v

class PromptRecord(PromptRegistration):
    registered_at: datetime = Field(default_factory=_utcnow)

class PromptVersionList(BaseModel):
    prompt_id: str
    versions: list

class CostBreakdownItem(BaseModel):
    calling_system: str
    task_type: str
    model: str
    calls: int
    cost_usd: float
    cache_hits: int

class CostResponse(BaseModel):
    period: dict
    total_cost_usd: float
    total_calls: int
    total_tokens_in: int
    total_tokens_out: int
    cache_hit_rate: float
    breakdown: list

class SystemAllocation(BaseModel):
    weight: float
    reserved_rpm: int

class LimitsResponse(BaseModel):
    provider_limits: dict
    per_system_allocation: dict

class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "sd-llm-service"
    version: str = "1.0.0"
    environment: str
    anthropic_reachable: bool
    cache_reachable: bool
    checked_at: datetime = Field(default_factory=_utcnow)

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    call_id: Optional[str] = None
