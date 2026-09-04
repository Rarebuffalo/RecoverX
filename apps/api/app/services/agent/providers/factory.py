from app.core.config import settings
from app.services.agent.providers.base_provider import BaseLLMProvider
from app.services.agent.providers.mock_provider import LocalDeterministicMockLLM
from app.services.agent.providers.gemini_provider import GeminiLLMProvider
from app.services.agent.providers.openai_provider import OpenAILLMProvider


def get_llm_provider(provider_override: str | None = None) -> BaseLLMProvider:
    """Returns the configured LLM provider instance with safe fallback to mock."""
    provider_type = (provider_override or settings.LLM_PROVIDER).lower().strip()

    if provider_type == "gemini":
        api_key = settings.LLM_API_KEY or settings.GEMINI_API_KEY
        if api_key:
            return GeminiLLMProvider(api_key=api_key, model=settings.LLM_MODEL or "gemini-2.5-flash")
    elif provider_type in ["openai", "gpt"]:
        api_key = settings.LLM_API_KEY or settings.OPENAI_API_KEY
        if api_key:
            return OpenAILLMProvider(api_key=api_key, model=settings.LLM_MODEL or "gpt-4o-mini")

    # Default to Local Deterministic Mock Provider for offline/zero-cost operation
    return LocalDeterministicMockLLM()
