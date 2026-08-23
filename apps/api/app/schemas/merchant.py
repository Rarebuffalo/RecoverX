import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


class MerchantPolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    auto_recovery_enabled: bool
    max_retry_attempts: int
    cooldown_minutes: int
    max_auto_recovery_amount_inr: Decimal
    max_customer_contact_per_day: int
    escalation_after_failed_attempts: int
    allowed_actions: list[str]
    created_at: datetime
    updated_at: datetime


class MerchantBase(BaseModel):
    name: str
    email: EmailStr
    razorpay_account_id: str | None = None
    is_active: bool = True


class MerchantCreate(MerchantBase):
    pass


class MerchantRead(MerchantBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    policy: MerchantPolicyRead | None = None
