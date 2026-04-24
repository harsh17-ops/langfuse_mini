import json

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.observability import PlaygroundResult, TraceCreateResponse
from app.services.evaluation_service import EvaluationService
from app.services.groq_client import GroqClient
from app.services.observability_service import ObservabilityService
from app.services.retrieval_service import RetrievalService


class LLMObserver:
    """
    Central observability wrapper.

    Every model call is represented as a trace, one or more spans, and one
    generation. This mirrors the Langfuse-style hierarchy and ensures logging,
    latency tracking, token tracking, and scoring happen in one place.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.groq_client = GroqClient()
        self.evaluation_service = EvaluationService()
        self.retrieval_service = RetrievalService()

    async def run_and_log(
        self,
        db: Session,
        *,
        name: str,
        prompt: str,
        model_name: str | None,
        session_id: str | None,
        user_id: str | None,
        background_tasks: BackgroundTasks | None = None,
        prompt_template_name: str | None = None,
        prompt_template_version: int | None = None,
        use_retrieval: bool = False,
        knowledge_base: list[str] | None = None,
    ) -> TraceCreateResponse:
        trace = ObservabilityService.create_trace(db, name=name, input=prompt, session_id=session_id, user_id=user_id)
        root_span = ObservabilityService.create_span(db, trace_id=trace.id, name="generation", type="LLM")
        retrieved_chunks: list[dict] = []
        prompt_for_generation = prompt

        if use_retrieval:
            retrieval_span = ObservabilityService.create_span(
                db,
                trace_id=trace.id,
                name="retrieval",
                type="RETRIEVAL",
                parent_span_id=root_span.id,
            )
            retrieved_chunks = self.retrieval_service.retrieve(prompt, knowledge_base=knowledge_base)
            retrieval_span.latency_ms = 5.0
            retrieval_span.metadata_json = self.retrieval_service.build_retrieval_metadata(retrieved_chunks)
            prompt_for_generation = self.retrieval_service.build_augmented_prompt(prompt, retrieved_chunks)
            ObservabilityService.create_score(
                db,
                trace_id=trace.id,
                generation_id=None,
                name="retrieval_context_count",
                value=len(retrieved_chunks),
                data_type="NUMERIC",
                source="retrieval",
            )

        llm_result = await self.groq_client.chat(prompt_for_generation, model_name)
        generation = ObservabilityService.create_generation(
            db,
            span_id=root_span.id,
            model=llm_result["model_name"],
            prompt=prompt_for_generation,
            response=llm_result["response"],
            prompt_tokens=llm_result["prompt_tokens"],
            completion_tokens=llm_result["completion_tokens"],
            total_tokens=llm_result["total_tokens"],
            latency_ms=llm_result["latency_ms"],
            cost_usd=llm_result["cost_usd"],
            prompt_template_name=prompt_template_name,
            prompt_template_version=prompt_template_version,
        )

        if self.settings.enable_model_evals:
            semantic_similarity = self.evaluation_service.score_semantic_similarity(prompt, llm_result["response"])
            classifier_scores = self.evaluation_service.classify_response(llm_result["response"])
            grounded_overlap = self.retrieval_service.grounded_overlap(llm_result["response"], retrieved_chunks) if retrieved_chunks else 0.0
            ObservabilityService.create_score(
                db,
                trace_id=trace.id,
                generation_id=generation.id,
                name="semantic_similarity",
                value=semantic_similarity,
                data_type="NUMERIC",
                source="model",
            )
            if use_retrieval:
                ObservabilityService.create_score(
                    db,
                    trace_id=trace.id,
                    generation_id=generation.id,
                    name="grounded_overlap",
                    value=grounded_overlap,
                    data_type="NUMERIC",
                    source="retrieval",
                )
            for score_name, score_value in classifier_scores.items():
                ObservabilityService.create_score(
                    db,
                    trace_id=trace.id,
                    generation_id=generation.id,
                    name=score_name,
                    value=score_value,
                    data_type="NUMERIC",
                    source="model",
                )

        ObservabilityService.finalize_trace(
            db,
            trace=trace,
            output=llm_result["response"],
            status="success",
            generation=generation,
            span=root_span,
        )

        if background_tasks and self.settings.enable_judge_evals:
            background_tasks.add_task(
                self.evaluation_service.run_judge_in_background,
                trace.id,
                generation.id,
                prompt_for_generation,
                llm_result["response"],
            )

        return TraceCreateResponse(
            trace_id=trace.id,
            generation_id=generation.id,
            response=llm_result["response"],
            model_name=llm_result["model_name"],
            latency_ms=llm_result["latency_ms"],
            prompt_tokens=llm_result["prompt_tokens"],
            completion_tokens=llm_result["completion_tokens"],
            total_tokens=llm_result["total_tokens"],
            cost_usd=llm_result["cost_usd"],
        )

    async def compare_models(
        self,
        *,
        prompt: str,
        primary_model: str,
        secondary_model: str,
    ) -> list[PlaygroundResult]:
        results: list[PlaygroundResult] = []
        for model_name in [primary_model, secondary_model]:
            llm_result = await self.groq_client.chat(prompt, model_name=model_name)
            semantic_similarity = self.evaluation_service.score_semantic_similarity(prompt, llm_result["response"])
            results.append(
                PlaygroundResult(
                    model_name=llm_result["model_name"],
                    response=llm_result["response"],
                    latency_ms=llm_result["latency_ms"],
                    total_tokens=llm_result["total_tokens"],
                    cost_usd=llm_result["cost_usd"],
                    semantic_similarity=semantic_similarity,
                )
            )
        return results
