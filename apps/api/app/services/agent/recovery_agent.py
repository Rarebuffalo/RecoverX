import time
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
from app.schemas.agent import RecoveryAgentContext, AgentProposal
from app.models.enums import RecoveryActionType, DiagnosisCategory
from app.services.agent.providers.factory import get_llm_provider
from app.services.agent.providers.base_provider import BaseLLMProvider
from app.core.logging import logger

PROMPT_VERSION = "recovery-diagnostic-v1"


@dataclass(frozen=True)
class AgentExecutionResult:
    proposal: AgentProposal
    provider: str
    model: str
    prompt_version: str
    status: str  # "SUCCESS", "FALLBACK"
    started_at: datetime
    completed_at: datetime
    latency_ms: int
    error_code: Optional[str] = None


class RecoveryAgent:
    """Diagnostic Reasoning Agent for payment recovery opportunities.

    PROPOSAL-ONLY BOUNDARY:
    The AI Agent produces structured proposals. It has zero access to payment execution APIs.
    """

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self.provider = provider or get_llm_provider()

    async def analyze(self, context: RecoveryAgentContext) -> AgentExecutionResult:
        started_at = datetime.now(timezone.utc)
        start_time = time.perf_counter()

        try:
            # 1. Generate Structured Proposal via Configured Provider
            proposal = await self.provider.generate_proposal(context)
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            completed_at = datetime.now(timezone.utc)

            # 2. Semantic Boundary Validation
            if proposal.recommended_action.value not in context.available_actions:
                logger.warning(
                    "Agent proposed action not in available actions, falling back to ESCALATE_TO_MERCHANT",
                    proposed=proposal.recommended_action.value,
                )
                proposal = AgentProposal(
                    diagnosis_category=proposal.diagnosis_category,
                    diagnosis_summary=proposal.diagnosis_summary,
                    recommended_action=RecoveryActionType.ESCALATE_TO_MERCHANT,
                    confidence=proposal.confidence,
                    fallback_action=RecoveryActionType.NO_ACTION,
                    decision_factors=proposal.decision_factors,
                )

            return AgentExecutionResult(
                proposal=proposal,
                provider=self.provider.provider_name,
                model=self.provider.model_name,
                prompt_version=PROMPT_VERSION,
                status="SUCCESS",
                started_at=started_at,
                completed_at=completed_at,
                latency_ms=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            completed_at = datetime.now(timezone.utc)
            logger.error("AI Agent execution error, executing safe fallback", error=str(e))

            # 3. Deterministic Safe Fallback
            fallback_proposal = AgentProposal(
                diagnosis_category=DiagnosisCategory.UNKNOWN,
                diagnosis_summary="Diagnostic model encountered an error or timeout. Routed to merchant escalation.",
                recommended_action=RecoveryActionType.ESCALATE_TO_MERCHANT,
                confidence=0.50,
                fallback_action=RecoveryActionType.NO_ACTION,
                decision_factors=["Provider failure fallback", f"Error: {type(e).__name__}"],
            )

            return AgentExecutionResult(
                proposal=fallback_proposal,
                provider=self.provider.provider_name,
                model=self.provider.model_name,
                prompt_version=PROMPT_VERSION,
                status="FALLBACK",
                started_at=started_at,
                completed_at=completed_at,
                latency_ms=elapsed_ms,
                error_code=type(e).__name__,
            )
