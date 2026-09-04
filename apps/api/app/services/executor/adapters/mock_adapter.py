import hashlib
from datetime import datetime, timezone
from app.services.executor.adapters.base_adapter import (
    BasePaymentGatewayAdapter,
    CreatePaymentLinkRequest,
    GatewayPaymentLinkResult,
)


class LocalDeterministicMockAdapter(BasePaymentGatewayAdapter):
    """Deterministic local mock adapter for offline testing, local dev, and synthetic benchmarks."""

    @property
    def adapter_name(self) -> str:
        return "local_deterministic"

    async def create_recovery_payment_link(
        self, request: CreatePaymentLinkRequest
    ) -> GatewayPaymentLinkResult:
        ref_hash = hashlib.sha256(request.reference_id.encode("utf-8")).hexdigest()[:12]
        provider_id = f"plink_mock_{ref_hash}"
        short_url = f"https://rzp.io/i/mock_{ref_hash}"

        now = datetime.now(timezone.utc)
        return GatewayPaymentLinkResult(
            provider_action_id=provider_id,
            payment_link_url=short_url,
            provider_reference_id=request.reference_id,
            status="created",
            created_at=now,
            raw_response={
                "id": provider_id,
                "short_url": short_url,
                "amount": request.amount_paise,
                "currency": request.currency,
                "reference_id": request.reference_id,
                "status": "created",
                "simulated": True,
            },
        )

    async def fetch_payment_link(self, provider_plink_id: str) -> dict:
        return {
            "id": provider_plink_id,
            "status": "created",
            "amount": 849900,
            "amount_paid": 0,
            "currency": "INR",
            "simulated": True,
        }

    async def fetch_payment_link_by_reference_id(self, reference_id: str) -> dict | None:
        ref_hash = hashlib.sha256(reference_id.encode("utf-8")).hexdigest()[:12]
        provider_id = f"plink_mock_{ref_hash}"
        return {
            "id": provider_id,
            "status": "created",
            "reference_id": reference_id,
            "amount": 849900,
            "amount_paid": 0,
            "currency": "INR",
            "simulated": True,
        }
