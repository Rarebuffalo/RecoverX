import pytest
from unittest.mock import patch, MagicMock
from app.services.executor.adapters.base_adapter import CreatePaymentLinkRequest
from app.services.executor.adapters.mock_adapter import LocalDeterministicMockAdapter
from app.services.executor.adapters.razorpay_adapter import RazorpaySandboxAdapter, GatewayExecutionException
from app.models.enums import ProviderErrorCategory


@pytest.mark.asyncio
async def test_mock_gateway_adapter():
    adapter = LocalDeterministicMockAdapter()
    req = CreatePaymentLinkRequest(
        amount_paise=849900,
        currency="INR",
        reference_id="rec_test_01",
        description="Test Recovery Link",
    )
    res = await adapter.create_recovery_payment_link(req)

    assert res.provider_action_id.startswith("plink_mock_")
    assert res.payment_link_url.startswith("https://rzp.io/i/mock_")
    assert res.status == "created"
    assert res.provider_reference_id == "rec_test_01"


@pytest.mark.asyncio
async def test_razorpay_adapter_error_classification():
    adapter = RazorpaySandboxAdapter(key_id="test_key", key_secret="test_secret")
    req = CreatePaymentLinkRequest(
        amount_paise=849900,
        currency="INR",
        reference_id="rec_test_02",
        description="Test Recovery Link",
    )

    # 1. 401 Authentication Error
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock(status_code=401, text="Unauthorized", json=lambda: {"error": {"description": "Invalid key"}})
        mock_post.return_value = mock_resp

        with pytest.raises(GatewayExecutionException) as exc:
            await adapter.create_recovery_payment_link(req)
        assert exc.value.category == ProviderErrorCategory.AUTHENTICATION_ERROR

    # 2. 500 Transient Error
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock(status_code=500, text="Internal Server Error", json=lambda: {})
        mock_post.return_value = mock_resp

        with pytest.raises(GatewayExecutionException) as exc:
            await adapter.create_recovery_payment_link(req)
        assert exc.value.category == ProviderErrorCategory.TRANSIENT_PROVIDER_ERROR
