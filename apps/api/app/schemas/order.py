import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.enums import OrderStatus
from app.schemas.customer import CustomerRead
from app.schemas.payment_attempt import PaymentAttemptRead


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    customer_id: uuid.UUID
    provider_order_id: str | None = None
    amount_inr: Decimal
    currency: str
    status: OrderStatus
    created_at: datetime
    updated_at: datetime


class OrderDetailRead(OrderRead):
    customer: CustomerRead | None = None
    payment_attempts: list[PaymentAttemptRead] = []
