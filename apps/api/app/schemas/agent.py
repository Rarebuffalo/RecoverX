from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from app.models.enums import RecoveryActionType, DiagnosisCategory


class OpportunityContext(BaseModel):
    id: str
    status: str
    revenue_at_risk_inr: float
    attempt_count: int


class OrderContext(BaseModel):
    amount_inr: float
    currency: str = "INR"
    status: str


class CustomerAggregateContext(BaseModel):
    """Sanitized customer behavioral statistics. ZERO PII."""
    successful_orders: int = 0
    total_orders: int = 0
    success_rate: float = 0.0
    lifetime_value_inr: float = 0.0


class PaymentAttemptContext(BaseModel):
    method: str
    failure_category: str
    failure_code: Optional[str] = None
    failure_reason: Optional[str] = None


class DeterministicScoreContext(BaseModel):
    score: int
    score_band: str
    eligibility: str


class PolicyLimitsContext(BaseModel):
    auto_recovery_enabled: bool
    max_retry_attempts: int
    cooldown_minutes: int
    max_auto_recovery_amount_inr: float
    allowed_actions: List[str]


class RecoveryAgentContext(BaseModel):
    """Sanitized, isolated context supplied to the AI Diagnostic Agent."""
    opportunity: OpportunityContext
    order: OrderContext
    customer: CustomerAggregateContext
    payment: PaymentAttemptContext
    recovery: DeterministicScoreContext
    policy: PolicyLimitsContext
    available_actions: List[str] = [
        RecoveryActionType.CREATE_RECOVERY_PAYMENT_LINK.value,
        RecoveryActionType.ESCALATE_TO_MERCHANT.value,
        RecoveryActionType.NO_ACTION.value,
    ]


class AgentProposal(BaseModel):
    """Strict structured output model produced by the AI Diagnostic Agent."""
    diagnosis_category: DiagnosisCategory
    diagnosis_summary: str = Field(..., max_length=500, description="Concise non-chain-of-thought factual diagnosis")
    recommended_action: RecoveryActionType
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model subjective confidence in diagnosis")
    fallback_action: RecoveryActionType = RecoveryActionType.ESCALATE_TO_MERCHANT
    decision_factors: List[str] = Field(default_factory=list, max_length=5, description="Up to 5 concise factual bullet points")

    @field_validator("decision_factors")
    def limit_decision_factors(cls, v: List[str]) -> List[str]:
        return [factor[:150] for factor in v[:5]]


class AgentDecisionRead(BaseModel):
    id: str
    opportunity_id: str
    agent_model: Optional[str]
    diagnosis_category: str
    recommended_action: str
    confidence_score: float
    reasoning_summary: str
    fallback_action: Optional[str]
    signals: dict
    policy_version: Optional[str]
    latency_ms: Optional[int]
    created_at: str
