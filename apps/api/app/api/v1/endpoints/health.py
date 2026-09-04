import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis
from app.core.config import settings
from app.db.session import get_db
from app.schemas.health import HealthResponse, ReadinessResponse, DependencyStatus, RuntimeStatusResponse

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
    """Readiness probe: verifies essential infrastructure dependencies (PostgreSQL and optional Redis)."""
    # 1. Check PostgreSQL (Primary data store)
    db_status = DependencyStatus(status="down")
    start_time = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        latency = (time.perf_counter() - start_time) * 1000
        db_status = DependencyStatus(status="ok", latency_ms=round(latency, 2))
    except Exception as e:
        db_status = DependencyStatus(status="down", error=str(e))

    # 2. Check Redis (Optional dependency)
    redis_status = DependencyStatus(status="disabled", latency_ms=0.0)
    if settings.REDIS_URL and settings.REDIS_URL.strip():
        start_time = time.perf_counter()
        try:
            r = aioredis.from_url(settings.REDIS_URL, socket_timeout=1.5)
            await r.ping()
            await r.aclose()
            latency = (time.perf_counter() - start_time) * 1000
            redis_status = DependencyStatus(status="ok", latency_ms=round(latency, 2))
        except Exception as e:
            redis_status = DependencyStatus(status="down", error=str(e))

    # If Postgres is healthy, service is ready (Redis is optional for direct async execution)
    if db_status.status == "ok":
        overall_status = "ok" if redis_status.status in ["ok", "disabled"] else "degraded"
    else:
        overall_status = "down"

    return ReadinessResponse(
        status=overall_status,
        database=db_status,
        redis=redis_status,
    )


@router.get("/runtime", response_model=RuntimeStatusResponse, tags=["Health"])
async def runtime_status():
    """Diagnostic probe: verifies active execution mode and gateway adapter selection without exposing secrets."""
    from app.services.executor.adapters.factory import get_gateway_adapter

    adapter = get_gateway_adapter()
    return RuntimeStatusResponse(
        execution_mode=settings.EXECUTION_MODE,
        adapter=adapter.__class__.__name__,
        has_razorpay_key_id=bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_ID.strip()),
        has_razorpay_key_secret=bool(settings.RAZORPAY_KEY_SECRET and settings.RAZORPAY_KEY_SECRET.strip()),
        has_razorpay_webhook_secret=bool(settings.RAZORPAY_WEBHOOK_SECRET and settings.RAZORPAY_WEBHOOK_SECRET.strip()),
        llm_provider=settings.LLM_PROVIDER,
        environment=settings.ENVIRONMENT,
    )

