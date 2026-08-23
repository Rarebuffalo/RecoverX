import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


class CustomerBase(BaseModel):
    email: EmailStr
    phone: str | None = None
    name: str | None = None


class CustomerRead(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    lifetime_value_inr: Decimal
    total_orders: int
    successful_orders: int
    created_at: datetime
    updated_at: datetime
