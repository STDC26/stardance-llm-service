from fastapi import APIRouter
emport httpx
from app.models.schemas import HealthResponse
from app.core.config import get_settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    settings = get_settings()
    anthropic_reachable = await _check_anthropic()
    cache_reachable = await _check_cache()
    return HealthResponse(status="ok" if anthropic_reachable else "degraded", service=settings.service_name, version=settings.service_version, environment=settings.environment, anthropic_reachable=anthropic_reachable, cache_reachable=cache_reachable)

async def _check_anthropic():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get("https://api.anthropic.com")
            return r.status_code < 500
    except: return False

async def _check_cache():
    try:
        import redis.asyncio as redis
        r = redis.from_url(get_settings().redis_url)
        await r.ping()
        await r.aclose()
        return True
    except: return False
