from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import health, llm, prompts, observability
from app.core.config import get_settings
import structlog

log = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    log.info("service_startup", service=s.service_name, version=s.service_version, environment=s.environment)
    yield
    log.info("service_shutdown", service=s.service_name)

def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title="SD Platform LLM Service", version=s.service_version, docs_url="/docs", redoc_url="/redoc", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(health.router, prefix="/v1/llm")
    app.include_router(llm.router, prefix="/v1/llm")
    app.include_router(prompts.router, prefix="/v1/llm")
    app.include_router(observability.router, prefix="/v1/llm")
    return app

app = create_app()
