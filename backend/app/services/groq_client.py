import time

import httpx

from app.core.config import get_settings
from app.services.token_counter import estimate_tokens


class GroqClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    async def chat(self, prompt: str, model_name: str | None = None) -> dict:
        model = model_name or self.settings.groq_model
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }

        start_time = time.perf_counter()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
        latency_ms = (time.perf_counter() - start_time) * 1000

        body = response.json()
        message = body["choices"][0]["message"]["content"]

        # Observability should prefer provider token counts when available.
        # If they are missing, we fall back to local estimation so the dashboard
        # still shows usage and cost signals.
        usage = body.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", estimate_tokens(prompt))
        completion_tokens = usage.get("completion_tokens", estimate_tokens(message))
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        return {
            "response": message,
            "model_name": model,
            "latency_ms": round(latency_ms, 2),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

