from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CreatePaymentLinkRequest(BaseModel):
    amount_paise: int = Field(..., gt=0, description="Amount in paise (e.g. 849900 for ₹8499.00)")
    currency: str = "INR"
    reference_id: str = Field(..., description="Unique idempotency reference key")
    description: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_contact: Optional[str] = None
    expire_by_timestamp: Optional[int] = None
    notes: Dict[str, Any] = Field(default_factory=dict)


@dataclass(frozen=True)
class GatewayPaymentLinkResult:
    provider_action_id: str
    payment_link_url: str
    provider_reference_id: str
    status: str
    created_at: datetime
    raw_response: Optional[Dict[str, Any]] = None


class BasePaymentGatewayAdapter(ABC):
    """Abstract interface for payment gateway execution adapters."""

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        pass

    @abstractmethod
    async def create_recovery_payment_link(
        self, request: CreatePaymentLinkRequest
    ) -> GatewayPaymentLinkResult:
        """Dispatches payment link creation to the payment gateway."""
        pass

    @abstractmethod
    async def fetch_payment_link(self, provider_plink_id: str) -> Dict[str, Any]:
        """Fetches status and details of an existing payment link from the gateway."""
        pass
