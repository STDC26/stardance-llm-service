from fastapi import APIRouter, HTTPException
from app.models.schemas import LLMCallRequest, LLMCallResponse
from app.services.router_service import RouterService
from app.services.cache_service import CacheService
from app.services.cost_service import CostService
from app.services.anthropic_service import AnthropicService
from app.core.config import get_settings
import time

router = APIRouter()
DETERMINISTIC_MODELS = {"rule_engine", "math_layer"}

@router.post("/call", response_model=LLMCallResponse, tags=["LLM"])
async def llm_call(request: LLMCallRequest):
    settings = get_settings()
    rule = RouterService(settings).resolve(request.task_type, request.high_stakes_flag)
    if rule["default_model"] in DETERMINISTIC_MODELS and not request.high_stakes_flag:
        raise HTTPException(status_code=422, detail=f"task_type '{request.task_type}' routes to deterministic layer. Call the appropriate service directly.")
    cache_svc = CacheService(settings)
    cost_svc = CostService(settings)
    anthropic_svc = AnthropicService(settings)
    prompt_version = request.prompt_version or "latest"
    start_time = time.time()
    cache_key = cache_svc.build_key(request.task_type, request.prompt_id, prompt_version, request.payload)
    if request.cache_eligible and request.cache_ttl_seconds > 0:
        cached = await cache_svc.get(cache_key)
        if cached:
            return LLMCallResponse(call_id=request.call_id, content=cached["content"], model_used=cached["model_used"], model_version=cached["model_version"], prompt_id=request.prompt_id, prompt_version=cached["prompt_version"], fallback_chain=[], cache_hit=True, tokens_in=cached["tokens_in"], tokens_out=cached["tokens_out"], cost_usd=0.0, latency_ms=int((time.time()-start_time)*1000), calling_system=request.calling_system, task_type=request.task_type)
    model_chain = [rule["default_model"]]
    if rule.get("fallback_model") and rule["fallback_model"] != rule["default_model"]: model_chain.append(rule["fallback_model"])
    fallback_chain, last_error = [], None
    for model in model_chain:
        try:
            result = await anthropic_svc.call(model=model, prompt_id=request.prompt_id, prompt_version=prompt_version, payload=request.payload, max_tokens=rule.get("max_tokens", 1024))
            fallback_chain.append(model)
            latency_ms = int((time.time()-start_time)*1000)
            cost = cost_svc.compute(model, result["tokens_in"], result["tokens_out"])
            await cost_svc.log(call_id=str(request.call_id), calling_system=request.calling_system, task_type=request.task_type, model=model, model_version=result["model_version"], tokens_in=result["tokens_in"], tokens_out=result["tokens_out"], cost_usd=cost, latency_ms=latency_ms, cache_hit=False, fallback_chain=fallback_chain)
            if request.cache_eligible and request.cache_ttl_seconds > 0: await cache_svc.set(cache_key, {"content": result["content"], "model_used": model, "model_version": result["model_version"], "prompt_version": result["prompt_version"], "tokens_in": result["tokens_in"], "tokens_out": result["tokens_out"]}, request.cache_ttl_seconds)
            return LLMCallResponse(call_id=request.call_id, content=result["content"], model_used=model, model_version=result["model_version"], prompt_id=request.prompt_id, prompt_version=result["prompt_version"], fallback_chain=fallback_chain, cache_hit=False, tokens_in=result["tokens_in"], tokens_out=result["tokens_out"], cost_usd=cost, latency_ms=latency_ms, calling_system=request.calling_system, task_type=request.task_type)
        except Exception as exc:
            fallback_chain.append(model)
            last_error = exc
    raise HTTPException(status_code=503, detail={"error": "All models exhausted", "fallback_chain": fallback_chain, "last_error": str(last_error)}, headers={"Retry-After": "30"})
