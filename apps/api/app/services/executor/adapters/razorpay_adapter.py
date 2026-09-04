import json
import httpx
from datetime import datetime, timezone
from typing import Optional
from app.services.executor.adapters.base_adapter import (
    BasePaymentGatewayAdapter,
    CreatePaymentLinkRequest,
    GatewayPaymentLinkResult,
)
from app.models.enums import ProviderErrorCategory
from app.core.config import settings
from app.core.logging import logger


class GatewayExecutionException(Exception):
    def __init__(self, category: ProviderErrorCategory, message: str, raw_response: Optional[dict] = None):
        super().__init__(message)
        self.category = category
        self.message = message
        self.raw_response = raw_response


class RazorpaySandboxAdapter(BasePaymentGatewayAdapter):
    """Adapter executing real Payment Link requests against Razorpay Test/Sandbox API."""

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        base_url: str = "https://api.razorpay.com/v1",
        timeout_seconds: float = 10.0,
    ):
        raw_key_id = key_id or settings.RAZORPAY_KEY_ID
        raw_key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.key_id = raw_key_id.strip() if raw_key_id else ""
        self.key_secret = raw_key_secret.strip() if raw_key_secret else ""
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @property
    def adapter_name(self) -> str:
        return "razorpay_sandbox"

    async def create_recovery_payment_link(
        self, request: CreatePaymentLinkRequest
    ) -> GatewayPaymentLinkResult:
        if not self.key_id or not self.key_secret:
            logger.error(
                "Razorpay credentials missing or incomplete in RazorpaySandboxAdapter",
                has_key_id=bool(self.key_id),
                has_key_secret=bool(self.key_secret),
            )
            raise GatewayExecutionException(
                ProviderErrorCategory.AUTHENTICATION_ERROR,
                "Razorpay API credentials (RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET) are not configured.",
            )

        # Razorpay API limits reference_id to max 40 characters
        ref_id = request.reference_id
        if len(ref_id) > 40:
            import hashlib
            ref_hash = hashlib.sha256(ref_id.encode("utf-8")).hexdigest()[:16]
            ref_id = f"rec_{ref_hash}"

        endpoint = f"{self.base_url}/payment_links"
        payload = {
            "amount": request.amount_paise,
            "currency": request.currency,
            "accept_partial": False,
            "reference_id": ref_id,
            "description": request.description[:255] if request.description else "RecoverX Payment Link",
            "reminder_enable": False,
            "notes": {str(k): str(v) for k, v in (request.notes or {}).items()},
        }

        if request.customer_email or request.customer_contact or request.customer_name:
            cust = {}
            if request.customer_name:
                cust["name"] = request.customer_name
            if request.customer_email:
                cust["email"] = request.customer_email
            if request.customer_contact:
                cust["contact"] = request.customer_contact
            payload["customer"] = cust

        if request.expire_by_timestamp:
            payload["expire_by"] = request.expire_by_timestamp

        auth = (self.key_id, self.key_secret)

        logger.info(
            "Dispatching HTTP POST to Razorpay Payment Links API",
            endpoint=endpoint,
            reference_id=ref_id,
            amount_paise=request.amount_paise,
            currency=request.currency,
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                res = await client.post(endpoint, json=payload, auth=auth)

                logger.info(
                    "Razorpay API response status received",
                    status_code=res.status_code,
                    reference_id=request.reference_id,
                )

                if res.status_code in [200, 201]:
                    data = res.json()
                    logger.info(
                        "Razorpay Payment Link created successfully",
                        provider_action_id=data.get("id", ""),
                        payment_link_url=data.get("short_url", ""),
                        reference_id=request.reference_id,
                    )
                    return GatewayPaymentLinkResult(
                        provider_action_id=data.get("id", ""),
                        payment_link_url=data.get("short_url", ""),
                        provider_reference_id=data.get("reference_id", request.reference_id),
                        status=data.get("status", "created"),
                        created_at=datetime.now(timezone.utc),
                        raw_response=data,
                    )

                # Error categorization
                res_data = {}
                try:
                    res_data = res.json()
                except Exception:
                    pass

                err_desc = res_data.get("error", {}).get("description", res.text)
                logger.error(
                    "Razorpay API returned error status",
                    status_code=res.status_code,
                    error_description=err_desc,
                    reference_id=request.reference_id,
                )

                if res.status_code in [401, 403]:
                    raise GatewayExecutionException(
                        ProviderErrorCategory.AUTHENTICATION_ERROR,
                        f"Razorpay Authentication Failed ({res.status_code}): {err_desc}",
                        res_data,
                    )
                elif res.status_code in [400, 422]:
                    raise GatewayExecutionException(
                        ProviderErrorCategory.VALIDATION_ERROR,
                        f"Razorpay Validation Error ({res.status_code}): {err_desc}",
                        res_data,
                    )
                elif res.status_code == 429:
                    raise GatewayExecutionException(
                        ProviderErrorCategory.RATE_LIMITED,
                        f"Razorpay Rate Limit Exceeded: {err_desc}",
                        res_data,
                    )
                elif res.status_code >= 500:
                    raise GatewayExecutionException(
                        ProviderErrorCategory.TRANSIENT_PROVIDER_ERROR,
                        f"Razorpay Server Error ({res.status_code}): {err_desc}",
                        res_data,
                    )
                else:
                    raise GatewayExecutionException(
                        ProviderErrorCategory.PERMANENT_PROVIDER_ERROR,
                        f"Razorpay Unexpected Status ({res.status_code}): {err_desc}",
                        res_data,
                    )

        except httpx.TimeoutException as te:
            logger.error("Razorpay request timed out", reference_id=request.reference_id)
            raise GatewayExecutionException(
                ProviderErrorCategory.TIMEOUT,
                f"Gateway request timed out after {self.timeout_seconds}s.",
            )
        except GatewayExecutionException:
            raise
        except Exception as e:
            logger.error("Unexpected error during Razorpay call", error=str(e))
            raise GatewayExecutionException(
                ProviderErrorCategory.AMBIGUOUS,
                f"Unexpected gateway communication failure: {str(e)}",
            )
