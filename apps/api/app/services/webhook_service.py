import uuid
import hashlib
from typing import Any, Dict, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models import ProcessedWebhook, AuditEvent, ActorType
from app.schemas.webhook import WebhookProcessingResult
from app.services.event_handlers.payment_failed_handler import PaymentFailedHandler
from app.services.event_handlers.payment_captured_handler import PaymentCapturedHandler
from app.services.event_handlers.order_paid_handler import OrderPaidHandler
from app.services.event_handlers.payment_link_paid_handler import PaymentLinkPaidHandler


class WebhookService:
    """Central webhook ingestion, deduplication, and routing service."""

    # Explicitly supported event registry
    HANDLERS = {
        "payment.failed": PaymentFailedHandler(),
        "payment.captured": PaymentCapturedHandler(),
        "order.paid": OrderPaidHandler(),
        "payment_link.paid": PaymentLinkPaidHandler(),
    }

    @classmethod
    def extract_event_id(cls, payload: Dict[str, Any], event_id_header: str | None = None) -> str:
        """Extracts event_id from payload, headers, or computes a deterministic hash."""
        if event_id_header:
            return event_id_header.strip()

        if payload.get("event_id"):
            return str(payload["event_id"]).strip()

        if payload.get("id") and str(payload.get("id")).startswith("evt_"):
            return str(payload["id"]).strip()

        # Deterministic fallback hash based on (event, entity_id, created_at)
        event_type = payload.get("event", "unknown")
        entity_id = (
            payload.get("payload", {}).get("payment", {}).get("entity", {}).get("id")
            or payload.get("payload", {}).get("order", {}).get("entity", {}).get("id")
            or payload.get("payload", {}).get("payment_link", {}).get("entity", {}).get("id")
            or "no_entity"
        )
        created_at = payload.get("created_at", 0)

        digest = hashlib.sha256(f"{event_type}_{entity_id}_{created_at}".encode("utf-8")).hexdigest()[:24]
        return f"evt_det_{digest}"

    @classmethod
    async def process_webhook(
        cls,
        db: AsyncSession,
        payload: Dict[str, Any],
        event_id_header: str | None = None,
    ) -> WebhookProcessingResult:
        event_type = payload.get("event")
        account_id = payload.get("account_id")
        event_id = cls.extract_event_id(payload, event_id_header=event_id_header)

        if not event_type:
            raise ValueError("Webhook payload missing required 'event' field.")

        # 1. Atomic Idempotency Check: Attempt to register in processed_webhooks
        # Check if already processed
        query = select(ProcessedWebhook).where(
            ProcessedWebhook.provider == "razorpay",
            ProcessedWebhook.event_id == event_id,
        ).with_for_update()
        existing = await db.execute(query)
        if existing.scalar_one_or_none():
            logger.info(
                "Duplicate webhook event ignored",
                event_id=event_id,
                event_type=event_type,
            )
            return WebhookProcessingResult(
                status="already_processed",
                event_id=event_id,
                event_type=event_type,
                message="Event has already been processed.",
            )

        # 2. Insert new processed_webhook record
        record = ProcessedWebhook(
            id=uuid.uuid4(),
            provider="razorpay",
            event_id=event_id,
            event_type=event_type,
            payload=payload,
        )
        db.add(record)
        await db.flush()

        # 3. Check Event Allowlist
        handler = cls.HANDLERS.get(event_type)
        if not handler:
            logger.info(
                "Unsupported webhook event acknowledged without business execution",
                event_id=event_id,
                event_type=event_type,
            )
            await db.commit()
            return WebhookProcessingResult(
                status="ignored_unsupported",
                event_id=event_id,
                event_type=event_type,
                message=f"Event type '{event_type}' is acknowledged but not handled in current phase.",
            )

        # 4. Execute Domain Event Handler
        try:
            result = await handler.handle(
                db=db,
                event_id=event_id,
                event_type=event_type,
                payload=payload,
                account_id=account_id,
            )
            await db.commit()

            return WebhookProcessingResult(
                status="processed",
                event_id=event_id,
                event_type=event_type,
                message="Event successfully processed and synchronized.",
            )
        except Exception as e:
            await db.rollback()
            logger.error(
                "Failed to process webhook event",
                event_id=event_id,
                event_type=event_type,
                error=str(e),
            )
            raise
