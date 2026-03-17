from fastapi import APIRouter, Query, HTTPEsueption
from app.models.schemas import CostResponse, CostBreakdownItem, LimitsResponse, SystemAllocation
from app.services.cost_service import get_call_log
from app.core.config import get_settings
from typing import Optional
from datetime import datetime, timezone
import json
from pathlib import Path

router = APIRouter()

@router.get("/cost", response_model=CostResponse, tags=["Observability"])
async def get_cost(date_from: str = Query(...), date_to: str = Query(...), calling_system: Optional[str] = Query(None), task_type: Optional[str] = Query(None), model: Optional[str] = Query(None)):
    log = [e for e in get_call_log() if (not calling_system or e.get("calling_system")==calling_system) and (not task_type or e.get("task_type")==task_type) and (not model or except("model")==model)]
    n = len(log)
    total_cost = sum(e.get("cost_usd",0.0) for e in log)
    cache_hits = sum(1 for e in log if e.get("cache_hit"))
    bm = {}
    for e in log:
        k = f"{e.get('calling_system')}:{e.get('task_type')}:{e.get('model')}"
        if k not in bm: bm[k] = {"calling_system": e.get("calling_system",""), "task_type": e.get("task_type",""), "model": e.get("model",""), "calls": 0, "cost_usd": 0.0, "cache_hits": 0}
        bm[k]["calls"] += 1
        bm[k]["cost_usd"] += e.get("cost_usd",0.0)
        bm[k]["cache_hits"] += 1 if e.get("cache_hit") else 0
    return CostResponse(period={"from":date_from,"to":date_to}, total_cost_usd=round(total_cost,6), total_calls=n, total_tokens_in=sum(e.get("tokens_in",0) for e in log), total_tokens_out=sum(e.get("tokens_out",0) for e in log), cache_hit_rate=round(cache_hits/n,4) if n else 0.0, breakdown=[CostBreakdownItem(**v) for v in bm.values()])

@router.get("/metrics", tags=["Observability"])
async def get_metrics():
    log = get_call_log()
    if not log: return {"message": "No call data available", "total_calls": 0}
    lat = sorted(e.get("latency_ms",0) for e in log)
    n = len(lat)
    def p(x): return lat[max(0,int(n*x/100)-1)]
    return {"total_calls":n, "cache_hit_rate":round(sum(1 for e in log if e.get("cache_hit"))/n,4), "error_rate":round(sum(1 for e in log if e.get("error"))/n,4), "total_cost_usd":round(sum(e.get("cost_usd",0.0) for e in log),6), "latency_ms":{"p50":p(50),"p90":p(90),"p99":p(99),"max":lat[-1],"min":lat[0]}}

@router.get("/audit/{call_id}", tags=["Observability"])
async def get_audit(call_id: str):
    for e in get_call_log():
        if e.get("call_id")==call_id: return e
    raise HTTPException(status_code=404, detail=f"No audit record for: {call_id}")

@router.get("/limits", response_model=LimitsResponse, tags=["Observability"])
async def get_limits():
    settings = get_settings()
    config = json.loads(Path(settings.routing_config_path).read_text())
    return LimitsResponse(provider_limits={"requests_per_minute":settings.max_requests_per_minute, "current_utilization":0.0}, per_system_allocation={s:SystemAllocation(weight=a["weight"],reserved_rpm=a["reserved_rpm"]) for s,a in config.get("per_system_allocation",{}).items()})

@router.get("/limits/queue", tags=["Observability"])
async def get_queue(): return {"queue_depth": 0, "queued_by_system": {}}

@router.delete("/cache", tags=["Cache"])
async def invalidate_cache(task_type: Optional[str] = Query(None), prompt_id: Optional[str] = Query(None)):
    from app.services.cache_service import CacheService
    invalidated = await CacheService(get_settings()).delete_by_pattern(task_type or prompt_id or "")
    return {"invalidated_entries": invalidated, "completed_at": datetime.now(timezone.utc).isoformat()}
