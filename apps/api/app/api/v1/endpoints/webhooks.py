import json
from fastapi import APIRouter, Request, Header, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logging import logger
from app.db.session import get_db
from app.schemas.webhook import WebhookProcessingResult
from app.services.webhook_verifier import WebhookSignatureVerifier
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/razorpay", response_model=WebhookProcessingResult)
async def receive_razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_razorpay_signature: str | None = Header(None, alias="X-Razorpay-Signature"),
    x_razorpay_event_id: str | None = Header(None, alias="X-Razorpay-Event-Id"),
):
    """Secure webhook ingestion endpoint for Razorpay payment and order events.

    1. Captures exact raw HTTP request body bytes.
    2. Performs constant-time HMAC-SHA256 signature verification.
    3. Enforces atomic idempotency on (provider, event_id).
    4. Executes domain state synchronization.
    5. Acknowledges with HTTP 200.
    """
    # 1. Capture Raw Request Body Bytes
    raw_body = await request.body()
    if not raw_body:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty request body.",
        )

    # 2. Cryptographic HMAC Signature Verification
    # In development/test mode without configured secret, allow a fallback development test secret
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET or "dev_razorpay_webhook_secret_123"

    is_valid = WebhookSignatureVerifier.verify(
        raw_body=raw_body,
        signature=x_razorpay_signature,
        secret=webhook_secret,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Razorpay webhook signature.",
        )

    # 3. Parse JSON only after signature verification
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        logger.error("Failed to parse verified webhook body as JSON", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload format.",
        )

    # 4. Atomic Idempotency & Domain Processing
    try:
        result = await WebhookService.process_webhook(
            db=db,
            payload=payload,
            event_id_header=x_razorpay_event_id,
        )
        return result
    except Exception as e:
        logger.error("Error processing webhook in service layer", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error synchronizing webhook event with database.",
        )
