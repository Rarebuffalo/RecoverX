import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import Integer, Numeric, DateTime, ForeignKey, Index, Uuid, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import OpportunityStatus


class RecoveryOpportunity(Base):
    __tablename__ = "recovery_opportunities"
    __table_args__ = (
        Index("idx_recovery_opps_merchant_status", "merchant_id", "status"),
        Index("idx_recovery_opps_created", "created_at"),
        Index("idx_recovery_opps_next_retry", "next_retry_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    status: Mapped[OpportunityStatus] = mapped_column(
        SAEnum(OpportunityStatus, native_enum=False, length=50),
        default=OpportunityStatus.DETECTED,
        nullable=False,
    )
    revenue_at_risk_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    recovered_amount_inr: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    recovery_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="recovery_opportunities")
    order: Mapped["Order"] = relationship("Order", back_populates="recovery_opportunity")
    decisions: Mapped[list["RecoveryDecision"]] = relationship(
        "RecoveryDecision", back_populates="opportunity", cascade="all, delete-orphan", order_by="RecoveryDecision.created_at"
    )
    actions: Mapped[list["RecoveryAction"]] = relationship(
        "RecoveryAction", back_populates="opportunity", cascade="all, delete-orphan", order_by="RecoveryAction.created_at"
    )
