import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import (
    RecoveryOpportunity,
    Order,
    Customer,
    PaymentAttempt,
    Merchant,
    MerchantPolicy,
    RecoveryDecision,
    RecoveryAction,
    AuditEvent,
    AgentRun,
    ActorType,
    OpportunityStatus,
    OrderStatus,
    ActionExecutionStatus,
)
from app.services.recovery_scoring_service import RecoveryScoringService, RecoveryScoreResult
from app.services.recovery_eligibility_service import RecoveryEligibilityService, EligibilityResult
from app.services.policy_engine import PolicyEngine, PolicyDecisionResult
from app.services.agent.context_builder import RecoveryContextBuilder
from app.services.agent.recovery_agent import RecoveryAgent, AgentExecutionResult
from app.schemas.agent import AgentProposal
from app.core.config import settings
from app.core.logging import logger


DEMO_ID_MAP = {
    "opp_demo_01": uuid.UUID("44444444-4444-4444-4444-444444444441"),
    "opp_demo_02": uuid.UUID("44444444-4444-4444-4444-444444444442"),
    "opp_demo_03": uuid.UUID("44444444-4444-4444-4444-444444444444"),
    "opp_demo_04": uuid.UUID("44444444-4444-4444-4444-444444444445"),
}


def resolve_opportunity_id(raw_id: str | uuid.UUID) -> uuid.UUID:
    if isinstance(raw_id, uuid.UUID):
        return raw_id
    if raw_id in DEMO_ID_MAP:
        return DEMO_ID_MAP[raw_id]
    try:
        return uuid.UUID(str(raw_id))
    except (ValueError, TypeError):
        return DEMO_ID_MAP.get(str(raw_id), uuid.UUID("44444444-4444-4444-4444-444444444441"))


class OpportunityService:
    @staticmethod
    async def get_by_id(
        db: AsyncSession, opportunity_id: uuid.UUID | str, merchant_id: uuid.UUID | str | None = None
    ) -> RecoveryOpportunity | None:
        target_id = resolve_opportunity_id(opportunity_id)
        query = (
            select(RecoveryOpportunity)
            .where(RecoveryOpportunity.id == target_id)
            .options(
                selectinload(RecoveryOpportunity.order).selectinload(Order.customer),
                selectinload(RecoveryOpportunity.order).selectinload(Order.payment_attempts),
                selectinload(RecoveryOpportunity.merchant).selectinload(Merchant.policy),
                selectinload(RecoveryOpportunity.actions),
                selectinload(RecoveryOpportunity.decisions),
            )
        )
        if merchant_id:
            query = query.where(RecoveryOpportunity.merchant_id == merchant_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_opportunities(
        db: AsyncSession,
        merchant_id: uuid.UUID | None = None,
        status_filter: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[RecoveryOpportunity]:
        query = (
            select(RecoveryOpportunity)
            .options(
                selectinload(RecoveryOpportunity.order).selectinload(Order.customer),
                selectinload(RecoveryOpportunity.order).selectinload(Order.payment_attempts),
                selectinload(RecoveryOpportunity.merchant).selectinload(Merchant.policy),
                selectinload(RecoveryOpportunity.actions),
                selectinload(RecoveryOpportunity.decisions),
            )
            .order_by(RecoveryOpportunity.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if merchant_id:
            query = query.where(RecoveryOpportunity.merchant_id == merchant_id)
        if status_filter:
            query = query.where(RecoveryOpportunity.status == status_filter)
        result = await db.execute(query)
        return list(result.scalars().all())

    @classmethod
    async def evaluate_opportunity(
        cls,
        db: AsyncSession,
        opportunity_id: uuid.UUID | str,
        merchant_id: uuid.UUID | str | None = None,
        proposed_action: str = "CREATE_PAYMENT_LINK",
        persist_decision: bool = True,
    ) -> Tuple[RecoveryScoreResult, EligibilityResult, PolicyDecisionResult]:
        opportunity = await cls.get_by_id(db, opportunity_id=opportunity_id, merchant_id=merchant_id)
        if not opportunity:
            raise ValueError(f"Recovery Opportunity '{opportunity_id}' not found.")

        order = opportunity.order
        customer = order.customer if order else None
        attempts = order.payment_attempts if order else []
        policy = opportunity.merchant.policy if opportunity.merchant else None
        existing_actions = opportunity.actions or []

        # 1. Deterministic Scoring
        scoring_service = RecoveryScoringService()
        score_result = scoring_service.calculate_score(
            opportunity=opportunity,
            order=order,
            customer=customer,
            attempts=attempts,
            policy=policy,
        )

        # 2. Deterministic Eligibility
        eligibility_result = RecoveryEligibilityService.evaluate(
            opportunity=opportunity,
            order=order,
            score_result=score_result,
            policy=policy,
        )

        # 3. Deterministic Policy Gate
        policy_decision = PolicyEngine.evaluate(
            proposed_action=proposed_action,
            opportunity=opportunity,
            order=order,
            score_result=score_result,
            policy=policy,
            existing_actions=existing_actions,
        )

        # 4. Optional Persistence of Decision & Audit Event
        if persist_decision:
            opportunity.recovery_score = score_result.score
            opportunity.updated_at = datetime.now(timezone.utc)

            confidence = Decimal(str(score_result.score / 100.0)).quantize(Decimal("0.001"))
            decision_record = RecoveryDecision(
                id=uuid.uuid4(),
                opportunity_id=opportunity.id,
                agent_model=None,
                policy_version=policy_decision.policy_version,
                diagnosis_category=score_result.failure_category,
                recommended_action=policy_decision.effective_action,
                confidence_score=confidence,
                reasoning_summary=score_result.explanation_summary,
                fallback_action="ESCALATE_TO_MERCHANT" if policy_decision.decision == "ESCALATE" else None,
                signals={
                    "score": score_result.score,
                    "score_band": score_result.score_band,
                    "feature_contributions": score_result.feature_contributions,
                    "eligibility_outcome": eligibility_result.outcome,
                    "eligibility_reasons": eligibility_result.reason_codes,
                    "policy_decision": policy_decision.decision,
                    "policy_reason_codes": policy_decision.reason_codes,
                },
            )
            db.add(decision_record)

            audit_event = AuditEvent(
                id=uuid.uuid4(),
                merchant_id=opportunity.merchant_id,
                opportunity_id=opportunity.id,
                actor_type=ActorType.SYSTEM,
                event_type=f"POLICY_{policy_decision.decision}",
                event_summary=f"Policy {policy_decision.decision}: {policy_decision.human_readable_summary}",
                event_data={
                    "score": score_result.score,
                    "score_band": score_result.score_band,
                    "policy_decision": policy_decision.decision,
                    "reason_codes": policy_decision.reason_codes,
                    "effective_action": policy_decision.effective_action,
                    "policy_version": policy_decision.policy_version,
                },
            )
            db.add(audit_event)
            await db.commit()

        return score_result, eligibility_result, policy_decision

    @classmethod
    async def agent_evaluate_opportunity(
        cls,
        db: AsyncSession,
        opportunity_id: uuid.UUID | str,
        merchant_id: uuid.UUID | str | None = None,
        provider_override: Optional[str] = None,
    ) -> Tuple[RecoveryScoreResult, EligibilityResult, AgentExecutionResult, PolicyDecisionResult]:
        """Runs the complete AI Diagnostic Agent pipeline: Context -> AI Proposal -> Policy Gate -> Persistence."""
        opportunity = await cls.get_by_id(db, opportunity_id=opportunity_id, merchant_id=merchant_id)
        if not opportunity:
            raise ValueError(f"Recovery Opportunity '{opportunity_id}' not found.")

        order = opportunity.order
        customer = order.customer if order else None
        attempts = order.payment_attempts if order else []
        policy = opportunity.merchant.policy if opportunity.merchant else None
        existing_actions = opportunity.actions or []

        # 1. Deterministic Scoring & Eligibility
        scoring_service = RecoveryScoringService()
        score_result = scoring_service.calculate_score(
            opportunity=opportunity,
            order=order,
            customer=customer,
            attempts=attempts,
            policy=policy,
        )
        eligibility_result = RecoveryEligibilityService.evaluate(
            opportunity=opportunity,
            order=order,
            score_result=score_result,
            policy=policy,
        )

        # 2. Build Sanitized Agent Context
        context = RecoveryContextBuilder.build_context(
            opportunity=opportunity,
            order=order,
            customer=customer,
            attempts=attempts,
            policy=policy,
            score_res=score_result,
            elig_res=eligibility_result,
        )

        # 3. Execute AI Diagnostic Agent
        agent = RecoveryAgent(provider=None if not provider_override else None)
        exec_result = await agent.analyze(context)

        # 4. Gated Validation by Deterministic Policy Engine
        policy_decision = PolicyEngine.evaluate(
            proposed_action=exec_result.proposal.recommended_action.value,
            opportunity=opportunity,
            order=order,
            score_result=score_result,
            policy=policy,
            existing_actions=existing_actions,
        )

        # 5. Persist Agent Run Record
        agent_run = AgentRun(
            id=uuid.uuid4(),
            opportunity_id=opportunity.id,
            provider=exec_result.provider,
            model=exec_result.model,
            prompt_version=exec_result.prompt_version,
            status=exec_result.status,
            started_at=exec_result.started_at,
            completed_at=exec_result.completed_at,
            latency_ms=exec_result.latency_ms,
            error_code=exec_result.error_code,
        )
        db.add(agent_run)

        # 6. Persist Structured Recovery Decision
        confidence_dec = Decimal(str(exec_result.proposal.confidence)).quantize(Decimal("0.001"))
        decision_record = RecoveryDecision(
            id=uuid.uuid4(),
            opportunity_id=opportunity.id,
            agent_model=f"{exec_result.provider}:{exec_result.model}",
            policy_version=policy_decision.policy_version,
            diagnosis_category=exec_result.proposal.diagnosis_category.value,
            recommended_action=exec_result.proposal.recommended_action.value,
            confidence_score=confidence_dec,
            reasoning_summary=exec_result.proposal.diagnosis_summary,
            fallback_action=exec_result.proposal.fallback_action.value,
            signals={
                "deterministic_score": score_result.score,
                "score_band": score_result.score_band,
                "eligibility": eligibility_result.outcome,
                "decision_factors": exec_result.proposal.decision_factors,
                "agent_status": exec_result.status,
                "agent_latency_ms": exec_result.latency_ms,
                "policy_decision": policy_decision.decision,
                "policy_reason_codes": policy_decision.reason_codes,
            },
            latency_ms=exec_result.latency_ms,
        )
        db.add(decision_record)

        # 7. Record Audit Event
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            merchant_id=opportunity.merchant_id,
            opportunity_id=opportunity.id,
            actor_type=ActorType.AGENT,
            event_type="AI_PROPOSAL_GENERATED",
            event_summary=(
                f"AI proposed '{exec_result.proposal.recommended_action.value}' "
                f"(Confidence: {exec_result.proposal.confidence:.2f}) -> Policy [{policy_decision.decision}]"
            ),
            event_data={
                "agent_run_id": str(agent_run.id),
                "model": exec_result.model,
                "diagnosis": exec_result.proposal.diagnosis_category.value,
                "proposed_action": exec_result.proposal.recommended_action.value,
                "confidence": exec_result.proposal.confidence,
                "policy_decision": policy_decision.decision,
                "policy_reasons": policy_decision.reason_codes,
            },
        )
        db.add(audit_event)

        # Update Opportunity score
        opportunity.recovery_score = score_result.score
        opportunity.updated_at = datetime.now(timezone.utc)
        await db.commit()

        return score_result, eligibility_result, exec_result, policy_decision

    @classmethod
    async def get_agent_decisions(
        cls, db: AsyncSession, opportunity_id: uuid.UUID | str
    ) -> List[RecoveryDecision]:
        target_id = resolve_opportunity_id(opportunity_id)
        query = (
            select(RecoveryDecision)
            .where(RecoveryDecision.opportunity_id == target_id)
            .order_by(RecoveryDecision.created_at.desc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @classmethod
    async def reconcile_opportunity(
        cls, db: AsyncSession, opportunity_id: uuid.UUID | str
    ) -> dict:
        """Reconciles recovery opportunity against verified webhook audit events or live gateway evidence."""
        target_id = resolve_opportunity_id(opportunity_id)
        opp = await cls.get_by_id(db, opportunity_id=target_id)
        if not opp:
            raise ValueError(f"Recovery Opportunity '{opportunity_id}' not found.")

        if opp.status == OpportunityStatus.RECOVERED:
            return {
                "status": "already_recovered",
                "opportunity_id": str(opp.id),
                "recovered_amount_inr": float(opp.recovered_amount_inr),
                "opportunity_status": opp.status.value,
                "message": "Opportunity is already marked as RECOVERED.",
            }

        now = datetime.now(timezone.utc)
        action_ids = [a.provider_action_id for a in (opp.actions or []) if a.provider_action_id]

        # 1. Check if there are already processed webhook audit events in database
        audit_query = select(AuditEvent).where(
            AuditEvent.event_type.in_([
                "PAYMENT_LINK_PAID_PROCESSED",
                "PAYMENT_CAPTURED_PROCESSED",
                "ORDER_PAID_PROCESSED",
                "REVENUE_RECOVERED",
            ])
        ).order_by(AuditEvent.created_at.desc())
        audit_res = await db.execute(audit_query)
        audits = audit_res.scalars().all()

        matched_event = None
        for a in audits:
            data = a.event_data or {}
            # Match by direct opportunity_id
            if a.opportunity_id == opp.id or str(data.get("opportunity_id")) == str(opp.id):
                matched_event = a
                break
            # Match by plink_id
            plink = data.get("provider_plink_id")
            if plink and plink in action_ids:
                matched_event = a
                break
            # Match by order_id
            if opp.order and data.get("provider_order_id") == opp.order.provider_order_id:
                matched_event = a
                break

        # 2. If matched from audit event, perform atomic state transition
        if matched_event:
            amount = Decimal(str(matched_event.event_data.get("amount_inr") or opp.revenue_at_risk_inr))
            opp.status = OpportunityStatus.RECOVERED
            opp.recovered_amount_inr = amount
            opp.resolved_at = now
            opp.updated_at = now
            if opp.order:
                opp.order.status = OrderStatus.PAID
                opp.order.updated_at = now
            if opp.actions:
                for act in opp.actions:
                    act.execution_status = ActionExecutionStatus.SUCCEEDED
                    act.completed_at = now

            db.add(AuditEvent(
                id=uuid.uuid4(),
                merchant_id=opp.merchant_id,
                opportunity_id=opp.id,
                actor_type=ActorType.SYSTEM,
                event_type="REVENUE_RECOVERED",
                event_summary=f"Reconciled recovery for {opp.id}: ₹{amount} from verified audit trail",
                event_data={
                    "opportunity_id": str(opp.id),
                    "recovered_amount_inr": str(amount),
                    "reconciliation_source": "audit_event_match",
                    "matched_event_id": str(matched_event.id),
                },
            ))
            await db.commit()
            await db.refresh(opp)
            return {
                "status": "reconciled",
                "opportunity_id": str(opp.id),
                "recovered_amount_inr": float(opp.recovered_amount_inr),
                "opportunity_status": opp.status.value,
                "message": f"Successfully reconciled recovery against verified event: {matched_event.event_type}",
            }

        # 3. Check live payment gateway if in razorpay_sandbox/live mode and action has plink_id
        if settings.EXECUTION_MODE == "razorpay_sandbox" and action_ids:
            try:
                from app.services.executor.adapters.factory import get_gateway_adapter
                adapter = get_gateway_adapter()
                for plink_id in action_ids:
                    plink_info = await adapter.fetch_payment_link(plink_id)
                    if plink_info.get("status") == "paid" or plink_info.get("amount_paid", 0) > 0:
                        raw_amt = plink_info.get("amount_paid") or plink_info.get("amount", 0)
                        amount = Decimal(str(raw_amt)) / Decimal("100.00")
                        opp.status = OpportunityStatus.RECOVERED
                        opp.recovered_amount_inr = amount
                        opp.resolved_at = now
                        opp.updated_at = now
                        if opp.order:
                            opp.order.status = OrderStatus.PAID
                            opp.order.updated_at = now
                        if opp.actions:
                            for act in opp.actions:
                                if act.provider_action_id == plink_id:
                                    act.execution_status = ActionExecutionStatus.SUCCEEDED
                                    act.completed_at = now

                        db.add(AuditEvent(
                            id=uuid.uuid4(),
                            merchant_id=opp.merchant_id,
                            opportunity_id=opp.id,
                            actor_type=ActorType.SYSTEM,
                            event_type="REVENUE_RECOVERED",
                            event_summary=f"Reconciled recovery for {opp.id}: ₹{amount} verified from Razorpay API",
                            event_data={
                                "opportunity_id": str(opp.id),
                                "recovered_amount_inr": str(amount),
                                "provider_plink_id": plink_id,
                                "reconciliation_source": "razorpay_api_fetch",
                            },
                        ))
                        await db.commit()
                        await db.refresh(opp)
                        return {
                            "status": "reconciled",
                            "opportunity_id": str(opp.id),
                            "recovered_amount_inr": float(opp.recovered_amount_inr),
                            "opportunity_status": opp.status.value,
                            "message": f"Successfully reconciled recovery against Razorpay API ({plink_id})",
                        }
            except Exception as e:
                logger.warning("Gateway link fetch during reconciliation failed", error=str(e))

        return {
            "status": "unreconciled",
            "opportunity_id": str(opp.id),
            "recovered_amount_inr": float(opp.recovered_amount_inr),
            "opportunity_status": opp.status.value,
            "message": "No verified payment evidence found for reconciliation.",
        }
