import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.enums import PaymentAttemptStatus


class PaymentAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    merchant_id: uuid.UUID
    provider_payment_id: str | None = None
    method: str
    status: PaymentAttemptStatus
    amount_inr: Decimal
    failure_code: str | None = None
    failure_reason: str | None = None
    created_at: datetime
    updated_at: datetime
