import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.enums import OpportunityStatus
from app.schemas.order import OrderRead


class RecoveryOpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    order_id: uuid.UUID
    status: OpportunityStatus
    revenue_at_risk_inr: Decimal
    recovered_amount_inr: Decimal
    recovery_score: int | None = None
    attempt_count: int
    last_attempt_at: datetime | None = None
    next_retry_at: datetime | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class RecoveryOpportunityDetailRead(RecoveryOpportunityRead):
    order: OrderRead | None = None
