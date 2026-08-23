import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_db
from app.models import RecoveryOpportunity, RecoveryAction, Order
from app.schemas.recovery_opportunity import RecoveryOpportunityDetailRead
from app.schemas.decision import (
    ScoreResponse,
    EligibilityResponse,
    PolicyDecisionResponse,
    EvaluationResponse,
)
from app.schemas.agent import AgentProposal, AgentDecisionRead
from app.services.opportunity_service import OpportunityService
from app.services.executor.action_executor_service import ActionExecutorService
from app.services.outcome.outcome_service import RecoveryOutcomeService

router = APIRouter(prefix="/opportunities", tags=["Recovery Opportunities"])


class AgentEvaluationResponse(BaseModel):
    opportunity_id: str
    order_id: str
    agent_model: str
    provider: str
    status: str
    latency_ms: int
    deterministic_score: ScoreResponse
    eligibility: EligibilityResponse
    ai_proposal: AgentProposal
    policy_decision: PolicyDecisionResponse


class ActionExecutionResponse(BaseModel):
    action_id: str
    opportunity_id: str
    action_type: str
    idempotency_key: str
    execution_status: str
    provider_action_id: Optional[str]
    payment_link_url: Optional[str]
    error_category: Optional[str]
    error_message: Optional[str]
    executed_at: Optional[str]
    completed_at: Optional[str]


class RecoveryMetricsResponse(BaseModel):
    total_opportunities: int
    recovered_opportunities: int
    active_opportunities: int
    total_revenue_at_risk_inr: float
    total_recovered_revenue_inr: float
    recovery_rate: float


@router.get("/metrics/summary", response_model=RecoveryMetricsResponse)
async def get_metrics_summary(db: AsyncSession = Depends(get_db)):
    """Computes aggregate recovery metrics across all opportunities."""
    metrics = await RecoveryOutcomeService.get_recovery_metrics(db)
    return RecoveryMetricsResponse(**metrics)


@router.get("", response_model=List[RecoveryOpportunityDetailRead])
async def list_opportunities_endpoint(
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List recovery opportunities with associated orders, customers, attempts, and actions."""
    return await OpportunityService.list_opportunities(
        db, status_filter=status, limit=limit, offset=offset
    )


@router.get("/{opportunity_id}", response_model=RecoveryOpportunityDetailRead)
async def get_opportunity(
    opportunity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve recovery opportunity details along with the associated order."""
    opportunity = await OpportunityService.get_by_id(db, opportunity_id=opportunity_id)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery Opportunity with ID {opportunity_id} not found.",
        )
    return opportunity


@router.get("/{opportunity_id}/score", response_model=ScoreResponse)
async def get_opportunity_score(
    opportunity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Computes and returns the deterministic recovery score and feature breakdown."""
    try:
        score_res, _, _ = await OpportunityService.evaluate_opportunity(
            db, opportunity_id=opportunity_id, persist_decision=False
        )
        opp = await OpportunityService.get_by_id(db, opportunity_id=opportunity_id)
        return ScoreResponse(
            opportunity_id=str(opportunity_id),
            order_id=str(opp.order_id) if opp else "",
            score=score_res.score,
            score_band=score_res.score_band,
            failure_category=score_res.failure_category,
            feature_contributions=score_res.feature_contributions,
            explanation_summary=score_res.explanation_summary,
            signals=score_res.signals,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{opportunity_id}/eligibility", response_model=EligibilityResponse)
async def get_opportunity_eligibility(
    opportunity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Evaluates and returns recovery eligibility."""
    try:
        score_res, elig_res, _ = await OpportunityService.evaluate_opportunity(
            db, opportunity_id=opportunity_id, persist_decision=False
        )
        return EligibilityResponse(
            opportunity_id=str(opportunity_id),
            eligible=elig_res.eligible,
            outcome=elig_res.outcome,
            score_band=elig_res.score_band,
            recommended_action_class=elig_res.recommended_action_class,
            reason_codes=elig_res.reason_codes,
            reason_summary=elig_res.reason_summary,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{opportunity_id}/policy-decision", response_model=PolicyDecisionResponse)
async def get_opportunity_policy_decision(
    opportunity_id: uuid.UUID,
    proposed_action: str = Query("CREATE_PAYMENT_LINK"),
    db: AsyncSession = Depends(get_db),
):
    """Evaluates the proposed action against deterministic policy rules."""
    try:
        _, _, policy_res = await OpportunityService.evaluate_opportunity(
            db,
            opportunity_id=opportunity_id,
            proposed_action=proposed_action,
            persist_decision=False,
        )
        return PolicyDecisionResponse(
            opportunity_id=str(opportunity_id),
            decision=policy_res.decision,
            effective_action=policy_res.effective_action,
            policy_version=policy_res.policy_version,
            reason_codes=policy_res.reason_codes,
            human_readable_summary=policy_res.human_readable_summary,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{opportunity_id}/evaluate", response_model=EvaluationResponse)
async def evaluate_opportunity_endpoint(
    opportunity_id: uuid.UUID,
    proposed_action: str = Query("CREATE_PAYMENT_LINK"),
    db: AsyncSession = Depends(get_db),
):
    """Executes deterministic evaluation chain (Scoring -> Eligibility -> Policy Gate) and logs decision."""
    try:
        score_res, elig_res, policy_res = await OpportunityService.evaluate_opportunity(
            db,
            opportunity_id=opportunity_id,
            proposed_action=proposed_action,
            persist_decision=True,
        )
        opp = await OpportunityService.get_by_id(db, opportunity_id=opportunity_id)

        return EvaluationResponse(
            opportunity_id=str(opportunity_id),
            order_id=str(opp.order_id) if opp else "",
            score=ScoreResponse(
                opportunity_id=str(opportunity_id),
                order_id=str(opp.order_id) if opp else "",
                score=score_res.score,
                score_band=score_res.score_band,
                failure_category=score_res.failure_category,
                feature_contributions=score_res.feature_contributions,
                explanation_summary=score_res.explanation_summary,
                signals=score_res.signals,
            ),
            eligibility=EligibilityResponse(
                opportunity_id=str(opportunity_id),
                eligible=elig_res.eligible,
                outcome=elig_res.outcome,
                score_band=elig_res.score_band,
                recommended_action_class=elig_res.recommended_action_class,
                reason_codes=elig_res.reason_codes,
                reason_summary=elig_res.reason_summary,
            ),
            policy_decision=PolicyDecisionResponse(
                opportunity_id=str(opportunity_id),
                decision=policy_res.decision,
                effective_action=policy_res.effective_action,
                policy_version=policy_res.policy_version,
                reason_codes=policy_res.reason_codes,
                human_readable_summary=policy_res.human_readable_summary,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{opportunity_id}/agent-evaluate", response_model=AgentEvaluationResponse)
async def agent_evaluate_opportunity_endpoint(
    opportunity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Executes the AI Diagnostic Agent to propose an action, gated by the Policy Engine."""
    try:
        score_res, elig_res, exec_res, policy_res = await OpportunityService.agent_evaluate_opportunity(
            db, opportunity_id=opportunity_id
        )
        opp = await OpportunityService.get_by_id(db, opportunity_id=opportunity_id)

        return AgentEvaluationResponse(
            opportunity_id=str(opportunity_id),
            order_id=str(opp.order_id) if opp else "",
            agent_model=exec_res.model,
            provider=exec_res.provider,
            status=exec_res.status,
            latency_ms=exec_res.latency_ms,
            deterministic_score=ScoreResponse(
                opportunity_id=str(opportunity_id),
                order_id=str(opp.order_id) if opp else "",
                score=score_res.score,
                score_band=score_res.score_band,
                failure_category=score_res.failure_category,
                feature_contributions=score_res.feature_contributions,
                explanation_summary=score_res.explanation_summary,
                signals=score_res.signals,
            ),
            eligibility=EligibilityResponse(
                opportunity_id=str(opportunity_id),
                eligible=elig_res.eligible,
                outcome=elig_res.outcome,
                score_band=elig_res.score_band,
                recommended_action_class=elig_res.recommended_action_class,
                reason_codes=elig_res.reason_codes,
                reason_summary=elig_res.reason_summary,
            ),
            ai_proposal=exec_res.proposal,
            policy_decision=PolicyDecisionResponse(
                opportunity_id=str(opportunity_id),
                decision=policy_res.decision,
                effective_action=policy_res.effective_action,
                policy_version=policy_res.policy_version,
                reason_codes=policy_res.reason_codes,
                human_readable_summary=policy_res.human_readable_summary,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{opportunity_id}/execute", response_model=ActionExecutionResponse)
async def execute_opportunity_action(
    opportunity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Executes the policy-approved recovery action and dispatches payment link creation."""
    try:
        # 1. Evaluate policy gate first
        score_res, elig_res, policy_res = await OpportunityService.evaluate_opportunity(
            db, opportunity_id=opportunity_id, persist_decision=False
        )

        if policy_res.decision != "ALLOW":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Execution blocked by Policy Gate [{policy_res.decision}]: {policy_res.human_readable_summary}",
            )

        # 2. Queue and execute action
        action = await ActionExecutorService.create_and_queue_action(
            db, opportunity_id=opportunity_id
        )
        executed_action, gw_result = await ActionExecutorService.execute_action(
            db, action_id=action.id
        )

        return ActionExecutionResponse(
            action_id=str(executed_action.id),
            opportunity_id=str(executed_action.opportunity_id),
            action_type=executed_action.action_type.value,
            idempotency_key=executed_action.idempotency_key,
            execution_status=executed_action.execution_status.value,
            provider_action_id=executed_action.provider_action_id,
            payment_link_url=executed_action.payment_link_url,
            error_category=executed_action.error_category,
            error_message=executed_action.error_message,
            executed_at=executed_action.executed_at.isoformat() if executed_action.executed_at else None,
            completed_at=executed_action.completed_at.isoformat() if executed_action.completed_at else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{opportunity_id}/actions", response_model=List[ActionExecutionResponse])
async def get_opportunity_actions(
    opportunity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Lists all historical recovery execution actions for this opportunity."""
    res = await db.execute(
        select(RecoveryAction)
        .where(RecoveryAction.opportunity_id == opportunity_id)
        .order_by(RecoveryAction.created_at.desc())
    )
    actions = res.scalars().all()
    return [
        ActionExecutionResponse(
            action_id=str(a.id),
            opportunity_id=str(a.opportunity_id),
            action_type=a.action_type.value,
            idempotency_key=a.idempotency_key,
            execution_status=a.execution_status.value,
            provider_action_id=a.provider_action_id,
            payment_link_url=a.payment_link_url,
            error_category=a.error_category,
            error_message=a.error_message,
            executed_at=a.executed_at.isoformat() if a.executed_at else None,
            completed_at=a.completed_at.isoformat() if a.completed_at else None,
        )
        for a in actions
    ]


@router.get("/{opportunity_id}/agent-decisions", response_model=List[AgentDecisionRead])
async def get_opportunity_agent_decisions(
    opportunity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all historical diagnostic decisions generated for this recovery opportunity."""
    decisions = await OpportunityService.get_agent_decisions(db, opportunity_id=opportunity_id)
    return [
        AgentDecisionRead(
            id=str(d.id),
            opportunity_id=str(d.opportunity_id),
            agent_model=d.agent_model,
            diagnosis_category=d.diagnosis_category,
            recommended_action=d.recommended_action,
            confidence_score=float(d.confidence_score),
            reasoning_summary=d.reasoning_summary,
            fallback_action=d.fallback_action,
            signals=d.signals,
            policy_version=d.policy_version,
            latency_ms=d.latency_ms,
            created_at=d.created_at.isoformat(),
        )
        for d in decisions
    ]
