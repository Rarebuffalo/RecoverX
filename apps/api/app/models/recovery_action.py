import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Index, Uuid, JSON, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.enums import RecoveryActionType, ActionExecutionStatus


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"
    __table_args__ = (
        Index("idx_recovery_actions_opp", "opportunity_id", "created_at"),
        Index("idx_recovery_actions_idempotency", "idempotency_key", unique=True),
        Index("idx_recovery_actions_status", "execution_status"),
        Index("idx_recovery_actions_provider_id", "provider_action_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("recovery_opportunities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    decision_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("recovery_decisions.id", ondelete="SET NULL"), nullable=True
    )
    action_type: Mapped[RecoveryActionType] = mapped_column(
        SAEnum(RecoveryActionType, native_enum=False, length=50),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    policy_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    policy_rejection_reasons: Mapped[list[str] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    execution_status: Mapped[ActionExecutionStatus] = mapped_column(
        SAEnum(ActionExecutionStatus, native_enum=False, length=50),
        default=ActionExecutionStatus.PENDING,
        nullable=False,
    )
    provider_action_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    payment_link_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    action_payload: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    execution_response: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    opportunity: Mapped["RecoveryOpportunity"] = relationship(
        "RecoveryOpportunity", back_populates="actions"
    )
    decision: Mapped["RecoveryDecision | None"] = relationship(
        "RecoveryDecision", back_populates="actions"
    )
