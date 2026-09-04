from datetime import datetime, timezone
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    environment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DependencyStatus(BaseModel):
    status: str
    latency_ms: float | None = None
    error: str | None = None


class ReadinessResponse(BaseModel):
    status: str  # ok, degraded, down
    database: DependencyStatus
    redis: DependencyStatus
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RuntimeStatusResponse(BaseModel):
    execution_mode: str
    adapter: str
    has_razorpay_key_id: bool
    has_razorpay_key_secret: bool
    has_razorpay_webhook_secret: bool
    llm_provider: str
    environment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

