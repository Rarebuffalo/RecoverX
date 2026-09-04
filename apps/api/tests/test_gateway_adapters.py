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


@pytest.mark.asyncio
async def test_factory_adapter_selection():
    from app.services.executor.adapters.factory import get_gateway_adapter
    from app.core.config import settings

    # Mode 1: razorpay_sandbox
    adapter = get_gateway_adapter("razorpay_sandbox")
    assert isinstance(adapter, RazorpaySandboxAdapter)
    assert adapter.adapter_name == "razorpay_sandbox"

    # Mode 2: local_deterministic
    adapter_mock = get_gateway_adapter("local_deterministic")
    assert isinstance(adapter_mock, LocalDeterministicMockAdapter)
    assert adapter_mock.adapter_name == "local_deterministic"


@pytest.mark.asyncio
async def test_razorpay_adapter_success_parsing():
    adapter = RazorpaySandboxAdapter(key_id="rzp_test_123", key_secret="secret_123")
    req = CreatePaymentLinkRequest(
        amount_paise=849900,
        currency="INR",
        reference_id="rec_test_success_01",
        description="Real Razorpay Test Link",
        customer_name="Rahul Sharma",
        customer_email="rahul@example.com",
    )

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock(
            status_code=200,
            json=lambda: {
                "id": "plink_G3Vp72HhW2bM4q",
                "short_url": "https://rzp.io/i/G3Vp72Hh",
                "status": "created",
                "reference_id": "rec_test_success_01",
                "amount": 849900,
            },
        )
        mock_post.return_value = mock_resp

        result = await adapter.create_recovery_payment_link(req)
        assert result.provider_action_id == "plink_G3Vp72HhW2bM4q"
        assert result.payment_link_url == "https://rzp.io/i/G3Vp72Hh"
        assert result.status == "created"
        assert result.provider_reference_id == "rec_test_success_01"


@pytest.mark.asyncio
async def test_razorpay_adapter_missing_credentials_raises():
    adapter = RazorpaySandboxAdapter(key_id="", key_secret="")
    req = CreatePaymentLinkRequest(
        amount_paise=849900,
        currency="INR",
        reference_id="rec_test_missing_creds",
        description="Test Missing Creds",
    )
    with pytest.raises(GatewayExecutionException) as exc:
        await adapter.create_recovery_payment_link(req)
    assert exc.value.category == ProviderErrorCategory.AUTHENTICATION_ERROR


@pytest.mark.asyncio
async def test_razorpay_adapter_reference_id_length_capped():
    adapter = RazorpaySandboxAdapter(key_id="rzp_test_123", key_secret="secret_123")
    # 55-char reference id
    long_ref_id = "recovery:44444444-4444-4444-4444-444444444441:attempt:1"
    req = CreatePaymentLinkRequest(
        amount_paise=849900,
        currency="INR",
        reference_id=long_ref_id,
        description="Test Long Ref ID",
    )

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock(
            status_code=200,
            json=lambda: {
                "id": "plink_G3Vp72HhW2bM4q",
                "short_url": "https://rzp.io/i/G3Vp72Hh",
                "status": "created",
                "reference_id": "rec_a1b2c3d4e5f67890",
            },
        )
        mock_post.return_value = mock_resp

        result = await adapter.create_recovery_payment_link(req)
        # Verify that payload sent to Razorpay had reference_id <= 40 chars
        called_payload = mock_post.call_args[1]["json"]
        assert len(called_payload["reference_id"]) <= 40
        assert called_payload["reference_id"].startswith("rec_")
        assert result.payment_link_url == "https://rzp.io/i/G3Vp72Hh"


