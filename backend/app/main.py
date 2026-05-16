from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.api.v1.router import api_router
from app.core.middleware import RequestLoggingMiddleware
import structlog

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Hackathon Eval Engine", env=settings.APP_ENV)
    yield
    logger.info("Shutting down Hackathon Eval Engine")


app = FastAPI(
    title="Hackathon Eval Engine",
    description="AI-powered hackathon evaluation platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(api_router, prefix="/api/v1")


@app.get("/api/health")
async def health_check():
    """Comprehensive health check for all dependencies."""
    from sqlalchemy import text
    from app.database import engine
    import httpx
    import redis.asyncio as aioredis

    checks = {"postgres": "unhealthy", "redis": "unhealthy", "ollama": "unhealthy"}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["postgres"] = "healthy"
    except Exception:
        pass

    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        checks["redis"] = "healthy"
    except Exception:
        pass

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/version")
            if resp.status_code == 200:
                checks["ollama"] = "healthy"
    except Exception:
        pass

    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    return {"status": overall, "env": settings.APP_ENV, "services": checks}
