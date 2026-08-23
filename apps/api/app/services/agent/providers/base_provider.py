from abc import ABC, abstractmethod
from app.schemas.agent import RecoveryAgentContext, AgentProposal


class BaseLLMProvider(ABC):
    """Abstract interface for LLM diagnostic proposal providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @abstractmethod
    async def generate_proposal(self, context: RecoveryAgentContext) -> AgentProposal:
        """Analyzes the sanitized context and returns a structured AgentProposal."""
        pass
