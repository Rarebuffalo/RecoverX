from typing import Any, Dict, List, Optional
from decimal import Decimal
from pydantic import BaseModel


class FeatureContributions(BaseModel):
    base_score: int
    failure_category: int
    customer_history: int
    customer_ltv: int
    attempt_penalty: int
    amount_risk: int
    recency_factor: int


class ScoreResponse(BaseModel):
    opportunity_id: str
    order_id: str
    score: int
    score_band: str
    failure_category: str
    feature_contributions: Dict[str, int]
    explanation_summary: str
    signals: Dict[str, Any]


class EligibilityResponse(BaseModel):
    opportunity_id: str
    eligible: bool
    outcome: str
    score_band: str
    recommended_action_class: str
    reason_codes: List[str]
    reason_summary: str


class PolicyDecisionResponse(BaseModel):
    opportunity_id: str
    decision: str
    effective_action: str
    policy_version: str
    reason_codes: List[str]
    human_readable_summary: str


class EvaluationResponse(BaseModel):
    opportunity_id: str
    order_id: str
    score: ScoreResponse
    eligibility: EligibilityResponse
    policy_decision: PolicyDecisionResponse
