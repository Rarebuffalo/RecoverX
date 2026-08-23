from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RazorpayWebhookPayload(BaseModel):
    entity: str = "event"
    account_id: Optional[str] = None
    event: str
    contains: List[str] = []
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[int] = None


class WebhookProcessingResult(BaseModel):
    status: str  # "processed", "already_processed", "ignored_unsupported"
    event_id: str
    event_type: str
    message: str
