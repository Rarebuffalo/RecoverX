import pytest
from pydantic import ValidationError
from app.schemas.agent import AgentProposal
from app.models.enums import RecoveryActionType, DiagnosisCategory


def test_agent_proposal_valid():
    proposal = AgentProposal(
        diagnosis_category=DiagnosisCategory.TRANSIENT_PAYMENT_FAILURE,
        diagnosis_summary="Gateway timeout on bank switch. Customer is loyal.",
        recommended_action=RecoveryActionType.CREATE_RECOVERY_PAYMENT_LINK,
        confidence=0.92,
        fallback_action=RecoveryActionType.ESCALATE_TO_MERCHANT,
        decision_factors=["Transient timeout", "High customer success rate"],
    )
    assert proposal.confidence == 0.92
    assert proposal.recommended_action == RecoveryActionType.CREATE_RECOVERY_PAYMENT_LINK


def test_agent_proposal_invalid_confidence():
    with pytest.raises(ValidationError):
        AgentProposal(
            diagnosis_category=DiagnosisCategory.TRANSIENT_PAYMENT_FAILURE,
            diagnosis_summary="Invalid confidence",
            recommended_action=RecoveryActionType.CREATE_RECOVERY_PAYMENT_LINK,
            confidence=1.5,  # > 1.0 invalid
        )

    with pytest.raises(ValidationError):
        AgentProposal(
            diagnosis_category=DiagnosisCategory.TRANSIENT_PAYMENT_FAILURE,
            diagnosis_summary="Negative confidence",
            recommended_action=RecoveryActionType.CREATE_RECOVERY_PAYMENT_LINK,
            confidence=-0.1,  # < 0.0 invalid
        )


def test_agent_proposal_invalid_diagnosis():
    with pytest.raises(ValidationError):
        AgentProposal(
            diagnosis_category="HALLUCINATED_CATEGORY",
            diagnosis_summary="Test",
            recommended_action=RecoveryActionType.CREATE_RECOVERY_PAYMENT_LINK,
            confidence=0.8,
        )
