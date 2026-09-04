import json
import httpx
from typing import Optional
from app.services.agent.providers.base_provider import BaseLLMProvider
from app.schemas.agent import RecoveryAgentContext, AgentProposal
from app.core.config import settings
from app.core.logging import logger
from app.services.agent.providers.gemini_provider import SYSTEM_PROMPT


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI standard chat completions provider with structured JSON output."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.LLM_API_KEY or settings.OPENAI_API_KEY
        self.model = model or (settings.LLM_MODEL if settings.LLM_PROVIDER == "openai" else "gpt-4o-mini")

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self.model

    async def generate_proposal(self, context: RecoveryAgentContext) -> AgentProposal:
        if not self.api_key:
            raise ValueError("OpenAI API key is not configured.")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        user_content = f"""<untrusted_recovery_context>
{context.model_dump_json(indent=2)}
</untrusted_recovery_context>

Based on the untrusted recovery context above, generate the structured diagnostic proposal adhering to the JSON schema:
{{
  "diagnosis_category": "TRANSIENT_PAYMENT_FAILURE" | "CUSTOMER_ACTION_REQUIRED" | "INSUFFICIENT_FUNDS" | "PAYMENT_METHOD_ISSUE" | "PERMANENT_PAYMENT_FAILURE" | "UNKNOWN",
  "diagnosis_summary": "Concise factual diagnosis...",
  "recommended_action": "CREATE_RECOVERY_PAYMENT_LINK" | "ESCALATE_TO_MERCHANT" | "NO_ACTION",
  "confidence": 0.0 to 1.0,
  "fallback_action": "ESCALATE_TO_MERCHANT" | "NO_ACTION",
  "decision_factors": ["factor 1", "factor 2"]
}}
"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        async with httpx.AsyncClient(timeout=float(settings.LLM_TIMEOUT_SECONDS)) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error("OpenAI API error", status_code=response.status_code, body=response.text)
                raise RuntimeError(f"OpenAI API returned status {response.status_code}")

            res_json = response.json()
            raw_text = res_json["choices"][0]["message"]["content"]
            data = json.loads(raw_text)
            return AgentProposal.model_validate(data)
