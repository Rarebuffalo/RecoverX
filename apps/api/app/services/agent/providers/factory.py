from app.core.config import settings
from app.services.agent.providers.base_provider import BaseLLMProvider
from app.services.agent.providers.mock_provider import LocalDeterministicMockLLM
from app.services.agent.providers.gemini_provider import GeminiLLMProvider


def get_llm_provider(provider_override: str | None = None) -> BaseLLMProvider:
    """Returns the configured LLM provider instance."""
    provider_type = (provider_override or settings.LLM_PROVIDER).lower().strip()

    if provider_type == "gemini" and settings.LLM_API_KEY:
        return GeminiLLMProvider()

    # Default to Local Deterministic Mock Provider for offline/zero-cost operation
    return LocalDeterministicMockLLM()
