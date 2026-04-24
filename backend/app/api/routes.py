import httpx

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.observability import (
    AnalyticsOverviewRead,
    DashboardStats,
    FeedbackRequest,
    PlaygroundCompareRequest,
    PlaygroundCompareResponse,
    PromptMetricsRead,
    PromptTemplateCreateRequest,
    PromptTemplateLabelRequest,
    PromptTemplateRead,
    PromptTemplateVersionRequest,
    ScoreFilterResponse,
    ScoreRead,
    TraceCreateRequest,
    TraceCreateResponse,
    TraceRead,
    TraceSummary,
)
from app.services.llm_observer import LLMObserver
from app.services.observability_service import ObservabilityService

router = APIRouter()
llm_observer = LLMObserver()


def _score_value(score) -> float | bool | str:
    if score.data_type == "BOOLEAN":
        return bool(score.value_boolean)
    if score.data_type == "CATEGORICAL":
        return score.value_categorical or ""
    return float(score.value_numeric or 0)


def _normalize_trace(trace) -> TraceRead:
    return TraceRead(
        id=trace.id,
        session_id=trace.session_id,
        user_id=trace.user_id,
        name=trace.name,
        input=trace.input,
        output=trace.output,
        status=trace.status,
        created_at=trace.created_at,
        spans=[
            {
                "id": span.id,
                "trace_id": span.trace_id,
                "parent_span_id": span.parent_span_id,
                "name": span.name,
                "type": span.type,
                "latency_ms": span.latency_ms,
                "status": span.status,
                "metadata_json": span.metadata_json,
                "created_at": span.created_at,
                "generations": [
                    {
                        "id": generation.id,
                        "span_id": generation.span_id,
                        "prompt_template_name": generation.prompt_template_name,
                        "prompt_template_version": generation.prompt_template_version,
                        "model": generation.model,
                        "prompt": generation.prompt,
                        "response": generation.response,
                        "prompt_tokens": generation.prompt_tokens,
                        "completion_tokens": generation.completion_tokens,
                        "total_tokens": generation.total_tokens,
                        "latency_ms": generation.latency_ms,
                        "cost_usd": generation.cost_usd,
                        "status": generation.status,
                        "error_message": generation.error_message,
                        "created_at": generation.created_at,
                    }
                    for generation in span.generations
                ],
            }
            for span in trace.spans
        ],
        scores=[
            {
                "id": score.id,
                "trace_id": score.trace_id,
                "generation_id": score.generation_id,
                "name": score.name,
                "value": _score_value(score),
                "data_type": score.data_type,
                "source": score.source,
                "created_at": score.created_at,
            }
            for score in trace.scores
        ],
    )


@router.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}


@router.post("/traces/generate", response_model=TraceCreateResponse)
async def create_generation_trace(
    payload: TraceCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> TraceCreateResponse:
    if not llm_observer.groq_client.settings.groq_api_key:
        raise HTTPException(status_code=500, detail="Missing GROQ_API_KEY in backend environment.")

    prompt_text = payload.input
    if payload.prompt_template_name:
        prompt_template = ObservabilityService.get_prompt_template(
            db,
            name=payload.prompt_template_name,
            version=payload.prompt_template_version,
        )
        if prompt_template:
            prompt_text = prompt_template.content.format(input=payload.input, user_input=payload.input)
            payload.prompt_template_version = prompt_template.version

    try:
        return await llm_observer.run_and_log(
            db,
            name=payload.name,
            prompt=prompt_text,
            model_name=payload.model_name,
            session_id=payload.session_id,
            user_id=payload.user_id,
            background_tasks=background_tasks,
            prompt_template_name=payload.prompt_template_name,
            prompt_template_version=payload.prompt_template_version,
            use_retrieval=payload.use_retrieval,
            knowledge_base=payload.knowledge_base,
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Groq API error: {exc.response.text}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Groq connectivity error: {str(exc)}") from exc


@router.post("/chat", response_model=TraceCreateResponse)
async def create_chat_completion(
    payload: TraceCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> TraceCreateResponse:
    return await create_generation_trace(payload, background_tasks, db)


@router.get("/traces", response_model=list[TraceSummary])
def list_traces(
    limit: int = Query(default=50, le=200),
    search: str | None = None,
    db: Session = Depends(get_db),
) -> list[TraceSummary]:
    return ObservabilityService.list_traces(db, limit=limit, search=search)


@router.get("/traces/{trace_id}", response_model=TraceRead)
def get_trace(trace_id: int, db: Session = Depends(get_db)) -> TraceRead:
    trace = ObservabilityService.get_trace(db, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return _normalize_trace(trace)


@router.post("/traces/{trace_id}/feedback", response_model=TraceRead)
def submit_feedback(trace_id: int, payload: FeedbackRequest, db: Session = Depends(get_db)) -> TraceRead:
    trace = ObservabilityService.submit_feedback(db, trace_id, payload.feedback)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return _normalize_trace(trace)


@router.get("/scores", response_model=list[ScoreRead])
def list_scores(trace_id: int | None = None, db: Session = Depends(get_db)) -> list[ScoreRead]:
    scores = ObservabilityService.list_scores(db, trace_id)
    normalized: list[ScoreRead] = []
    for score in scores:
        normalized.append(
            ScoreRead(
                id=score.id,
                trace_id=score.trace_id,
                generation_id=score.generation_id,
                name=score.name,
                value=_score_value(score),
                data_type=score.data_type,
                source=score.source,
                created_at=score.created_at,
            )
        )
    return normalized


@router.get("/scores/filter", response_model=ScoreFilterResponse)
def filter_by_score(score_name: str, min_value: float | None = None, db: Session = Depends(get_db)) -> ScoreFilterResponse:
    traces = ObservabilityService.filter_traces_by_score(db, score_name, min_value)
    return ScoreFilterResponse(traces=traces, score_name=score_name, min_value=min_value)


@router.get("/analytics/overview", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)) -> DashboardStats:
    return DashboardStats(**ObservabilityService.get_dashboard_stats(db))


@router.get("/analytics/deep", response_model=AnalyticsOverviewRead)
def get_deep_analytics(db: Session = Depends(get_db)) -> AnalyticsOverviewRead:
    return AnalyticsOverviewRead(**ObservabilityService.get_analytics_overview(db))


@router.get("/prompts", response_model=list[PromptTemplateRead])
def list_prompts(db: Session = Depends(get_db)) -> list[PromptTemplateRead]:
    return ObservabilityService.list_prompt_templates(db)


@router.post("/prompts", response_model=PromptTemplateRead)
def create_prompt(payload: PromptTemplateCreateRequest, db: Session = Depends(get_db)) -> PromptTemplateRead:
    return ObservabilityService.create_prompt_template(db, name=payload.name, content=payload.content, label=payload.label)


@router.post("/prompts/{name}", response_model=PromptTemplateRead)
def create_prompt_version(name: str, payload: PromptTemplateVersionRequest, db: Session = Depends(get_db)) -> PromptTemplateRead:
    return ObservabilityService.create_prompt_template(db, name=name, content=payload.content, label="staging")


@router.get("/prompts/{name}/production", response_model=PromptTemplateRead)
def get_production_prompt(name: str, db: Session = Depends(get_db)) -> PromptTemplateRead:
    prompt = ObservabilityService.get_prompt_by_label(db, name=name, label="production")
    if not prompt:
        raise HTTPException(status_code=404, detail="Production prompt not found")
    return prompt


@router.put("/prompts/{name}/{version}/label", response_model=PromptTemplateRead)
def promote_prompt(name: str, version: int, payload: PromptTemplateLabelRequest, db: Session = Depends(get_db)) -> PromptTemplateRead:
    prompt = ObservabilityService.promote_prompt_label(db, name=name, version=version, label=payload.label)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    return prompt


@router.get("/prompts/{name}/metrics", response_model=list[PromptMetricsRead])
def prompt_metrics(name: str, db: Session = Depends(get_db)) -> list[PromptMetricsRead]:
    return [PromptMetricsRead(**row) for row in ObservabilityService.get_prompt_metrics(db, name=name)]


@router.post("/playground/compare", response_model=PlaygroundCompareResponse)
async def compare_playground(payload: PlaygroundCompareRequest, db: Session = Depends(get_db)) -> PlaygroundCompareResponse:
    prompt_text = payload.prompt
    template_data = None
    if payload.prompt_template_name:
        prompt_template = ObservabilityService.get_prompt_template(
            db,
            name=payload.prompt_template_name,
            version=payload.prompt_template_version,
        )
        if prompt_template:
            prompt_text = prompt_template.content.format(input=payload.prompt, user_input=payload.prompt)
            template_data = {"name": prompt_template.name, "version": prompt_template.version, "label": prompt_template.label}
    results = await llm_observer.compare_models(
        prompt=prompt_text,
        primary_model=payload.primary_model,
        secondary_model=payload.secondary_model,
    )
    return PlaygroundCompareResponse(prompt=prompt_text, template=template_data, results=results)
