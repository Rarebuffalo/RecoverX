from app.core.config import settings
from app.services.executor.adapters.base_adapter import BasePaymentGatewayAdapter
from app.services.executor.adapters.mock_adapter import LocalDeterministicMockAdapter
from app.services.executor.adapters.razorpay_adapter import RazorpaySandboxAdapter


def get_gateway_adapter(mode_override: str | None = None) -> BasePaymentGatewayAdapter:
    """Returns the configured Payment Gateway Adapter."""
    mode = (mode_override or settings.EXECUTION_MODE).lower().strip()

    if mode == "razorpay_sandbox" and settings.RAZORPAY_KEY_ID:
        return RazorpaySandboxAdapter()

    # Default to Local Deterministic Mock Adapter
    return LocalDeterministicMockAdapter()
