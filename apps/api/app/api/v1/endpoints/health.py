import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis
from app.core.config import settings
from app.db.session import get_db
from app.schemas.health import HealthResponse, ReadinessResponse, DependencyStatus

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Liveness probe: verifies the API server is up and accepting requests."""
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
    )


@router.get("/ready", response_model=ReadinessResponse, tags=["Health"])
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness probe: verifies essential infrastructure dependencies (PostgreSQL and Redis)."""
    # 1. Check PostgreSQL
    db_status = DependencyStatus(status="down")
    start_time = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        latency = (time.perf_counter() - start_time) * 1000
        db_status = DependencyStatus(status="ok", latency_ms=round(latency, 2))
    except Exception as e:
        db_status = DependencyStatus(status="down", error=str(e))

    # 2. Check Redis
    redis_status = DependencyStatus(status="down")
    start_time = time.perf_counter()
    try:
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        await r.ping()
        await r.aclose()
        latency = (time.perf_counter() - start_time) * 1000
        redis_status = DependencyStatus(status="ok", latency_ms=round(latency, 2))
    except Exception as e:
        redis_status = DependencyStatus(status="down", error=str(e))

    overall_status = "ok" if (db_status.status == "ok" and redis_status.status == "ok") else "degraded"
    if db_status.status == "down" and redis_status.status == "down":
        overall_status = "down"

    return ReadinessResponse(
        status=overall_status,
        database=db_status,
        redis=redis_status,
    )
