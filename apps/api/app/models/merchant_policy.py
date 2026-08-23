import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import Boolean, Integer, Numeric, DateTime, ForeignKey, Index, Uuid, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class MerchantPolicy(Base):
    __tablename__ = "merchant_policies"
    __table_args__ = (
        Index("idx_merchant_policies_merchant", "merchant_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    auto_recovery_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_retry_attempts: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    max_auto_recovery_amount_inr: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("10000.00"), nullable=False
    )
    max_customer_contact_per_day: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    escalation_after_failed_attempts: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    allowed_actions: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=lambda: ["CREATE_PAYMENT_LINK", "SCHEDULE_MANDATE_RETRY", "CUSTOMER_REMINDER_SMS"],
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="policy")
