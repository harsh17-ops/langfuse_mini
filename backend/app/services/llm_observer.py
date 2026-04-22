from sqlalchemy.orm import Session

from app.schemas.llm_log import ChatResponse
from app.services.groq_client import GroqClient
from app.services.observability_service import ObservabilityService


class LLMObserver:
    """
    Logging wrapper around LLM calls.

    This class centralizes observability. Instead of routes talking directly
    to the provider, every request passes through this wrapper so latency,
    usage, model metadata, and outputs are consistently captured and stored.
    """

    def __init__(self) -> None:
        self.groq_client = GroqClient()

    async def run_and_log(self, db: Session, prompt: str, model_name: str | None = None) -> ChatResponse:
        llm_result = await self.groq_client.chat(prompt, model_name)
        log = ObservabilityService.create_log(
            db,
            prompt=prompt,
            response=llm_result["response"],
            model_name=llm_result["model_name"],
            latency_ms=llm_result["latency_ms"],
            prompt_tokens=llm_result["prompt_tokens"],
            completion_tokens=llm_result["completion_tokens"],
            total_tokens=llm_result["total_tokens"],
        )
        return ChatResponse(log_id=log.id, **llm_result)
