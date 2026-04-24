import asyncio
import json
import re
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.groq_client import GroqClient

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:  # pragma: no cover - optional runtime dependency
    SentenceTransformer = None
    util = None

try:
    from transformers import pipeline
except ImportError:  # pragma: no cover - optional runtime dependency
    pipeline = None


class EvaluationService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.groq_client = GroqClient()
        self._embedding_model = None
        self._classifier = None

    def _get_embedding_model(self):
        if SentenceTransformer is None:
            return None
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._embedding_model

    def _get_classifier(self):
        if pipeline is None:
            return None
        if self._classifier is None:
            self._classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        return self._classifier

    def score_semantic_similarity(self, prompt: str, response: str) -> float:
        model = self._get_embedding_model()
        if model is None or util is None:
            prompt_terms = set(prompt.lower().split())
            response_terms = set(response.lower().split())
            if not prompt_terms or not response_terms:
                return 0.0
            overlap = len(prompt_terms.intersection(response_terms))
            return round(overlap / max(len(prompt_terms), 1), 4)
        emb_prompt = model.encode(prompt, convert_to_tensor=True)
        emb_response = model.encode(response, convert_to_tensor=True)
        return round(float(util.cos_sim(emb_prompt, emb_response)), 4)

    def classify_response(self, response: str) -> dict[str, float]:
        classifier = self._get_classifier()
        labels = ["factual", "hallucinated", "toxic", "off-topic"]
        if classifier is None:
            lowered = response.lower()
            return {
                "factual": 0.7 if "because" in lowered or "is" in lowered else 0.4,
                "hallucinated": 0.2 if "maybe" not in lowered else 0.45,
                "toxic": 0.05,
                "off-topic": 0.15,
            }
        result = classifier(response, candidate_labels=labels)
        return {label: round(score, 4) for label, score in zip(result["labels"], result["scores"])}

    async def llm_judge_eval(self, prompt: str, response: str) -> dict[str, float]:
        judge_prompt = f"""Rate this LLM response on 4 dimensions and return JSON only.
Prompt: {prompt}
Response: {response}
Return: {{"relevance": 0-1, "coherence": 0-1, "groundedness": 0-1, "overall": 0-1}}"""
        result = await self.groq_client.chat(judge_prompt, model_name=self.settings.groq_judge_model)
        parsed = self._parse_json_object(result["response"])
        return {name: round(float(value), 4) for name, value in parsed.items() if isinstance(value, (int, float, str))}

    def run_judge_in_background(self, trace_id: int, generation_id: int, prompt: str, response: str) -> None:
        asyncio.run(self._run_judge_and_store(trace_id, generation_id, prompt, response))

    async def _run_judge_and_store(self, trace_id: int, generation_id: int, prompt: str, response: str) -> None:
        from app.services.observability_service import ObservabilityService

        if not self.settings.enable_judge_evals:
            return
        db: Session = SessionLocal()
        try:
            scores = await self.llm_judge_eval(prompt, response)
            for name, value in scores.items():
                ObservabilityService.create_score(
                    db,
                    trace_id=trace_id,
                    generation_id=generation_id,
                    name=name,
                    value=value,
                    data_type="NUMERIC",
                    source="llm_judge",
                )
            db.commit()
        except (httpx.HTTPError, json.JSONDecodeError, ValueError, TypeError):
            ObservabilityService.create_score(
                db,
                trace_id=trace_id,
                generation_id=generation_id,
                name="judge_status",
                value="failed",
                data_type="CATEGORICAL",
                source="llm_judge",
            )
            db.commit()
        finally:
            db.close()

    def _parse_json_object(self, raw_text: str) -> dict[str, Any]:
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))
