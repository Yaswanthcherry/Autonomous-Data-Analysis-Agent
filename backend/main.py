"""
AI Data Analyst Agent — FastAPI entry point
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.config import settings
from core.logging import setup_logging, RequestLoggingMiddleware
from core.database import engine, Base
from api.v1.router import api_router

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (idempotent — safe in development)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="AI Data Analyst Agent",
    version="1.0.0",
    description="Autonomous AI-powered data analysis platform",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/health/ready")
async def readiness():
    """Readiness check - verifies database and Redis connections."""
    try:
        # Check database
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        
        # Check Redis
        import redis.asyncio as redis
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        
        return {"status": "ready", "checks": {"database": "ok", "redis": "ok"}}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}


@app.get("/health/live")
async def liveness():
    """Liveness check - basic service availability."""
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}
