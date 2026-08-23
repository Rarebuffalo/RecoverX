import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Numeric, DateTime, ForeignKey, Index, Uuid, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class RecoveryDecision(Base):
    __tablename__ = "recovery_decisions"
    __table_args__ = (
        Index("idx_recovery_decisions_opp", "opportunity_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("recovery_opportunities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    policy_version: Mapped[str | None] = mapped_column(String(20), default="v1", nullable=True)
    diagnosis_category: Mapped[str] = mapped_column(String(100), nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    reasoning_summary: Mapped[str] = mapped_column(Text, nullable=False)
    fallback_action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    signals: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict, nullable=False
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    opportunity: Mapped["RecoveryOpportunity"] = relationship(
        "RecoveryOpportunity", back_populates="decisions"
    )
    actions: Mapped[list["RecoveryAction"]] = relationship(
        "RecoveryAction", back_populates="decision"
    )
