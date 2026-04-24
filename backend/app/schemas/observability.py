from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class TraceCreateRequest(BaseModel):
    name: str = Field(default="chat-request")
    session_id: str | None = None
    user_id: str | None = None
    input: str = Field(..., min_length=1)
    prompt: str | None = None
    model_name: str | None = None
    prompt_template_name: str | None = None
    prompt_template_version: int | None = None
    use_retrieval: bool = False
    knowledge_base: list[str] | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_prompt_alias(cls, data: Any) -> Any:
        if isinstance(data, dict) and "input" not in data and "prompt" in data:
            data["input"] = data["prompt"]
        return data


class ScoreRead(BaseModel):
    id: int
    trace_id: int
    generation_id: int | None
    name: str
    value: float | bool | str
    data_type: str
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerationRead(BaseModel):
    id: int
    span_id: int
    prompt_template_name: str | None
    prompt_template_version: int | None
    model: str
    prompt: str
    response: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float
    status: str
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SpanRead(BaseModel):
    id: int
    trace_id: int
    parent_span_id: int | None
    name: str
    type: str
    latency_ms: float
    status: str
    metadata_json: str | None
    created_at: datetime
    generations: list[GenerationRead] = []

    model_config = {"from_attributes": True}


class TraceRead(BaseModel):
    id: int
    session_id: str | None
    user_id: str | None
    name: str
    input: str
    output: str | None
    status: str
    created_at: datetime
    spans: list[SpanRead] = []
    scores: list[ScoreRead] = []

    model_config = {"from_attributes": True}


class TraceSummary(BaseModel):
    id: int
    name: str
    session_id: str | None
    user_id: str | None
    input: str
    output: str | None
    status: str
    created_at: datetime
    latest_generation_model: str | None
    latest_generation_latency_ms: float | None
    latest_generation_total_tokens: int | None
    overall_score: float | None
    semantic_similarity: float | None
    grounded_overlap: float | None
    human_feedback: str | None
    retrieval_used: bool
    prompt_family: str | None


class TraceCreateResponse(BaseModel):
    trace_id: int
    generation_id: int
    response: str
    model_name: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


class FeedbackRequest(BaseModel):
    feedback: Literal["up", "down"]


class DashboardStats(BaseModel):
    total_traces: int
    avg_latency_ms: float
    p95_latency_ms: float
    total_tokens: int
    total_cost_usd: float
    positive_feedback: int
    negative_feedback: int
    avg_overall_score: float
    avg_semantic_similarity: float
    avg_grounded_overlap: float
    retrieval_trace_count: int


class ModelUsageRead(BaseModel):
    model_name: str
    trace_count: int


class ScoreDistributionRead(BaseModel):
    score_name: str
    average: float


class AnalyticsOverviewRead(BaseModel):
    stats: DashboardStats
    model_usage: list[ModelUsageRead]
    score_distributions: list[ScoreDistributionRead]


class ScoreFilterResponse(BaseModel):
    traces: list[TraceSummary]
    score_name: str
    min_value: float | None


class PromptTemplateCreateRequest(BaseModel):
    name: str
    content: str
    label: str = "staging"


class PromptTemplateVersionRequest(BaseModel):
    content: str


class PromptTemplateLabelRequest(BaseModel):
    label: Literal["staging", "production"]


class PromptTemplateRead(BaseModel):
    id: int
    name: str
    version: int
    content: str
    label: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PromptMetricsRead(BaseModel):
    version: int
    label: str
    generations: int
    avg_overall_score: float
    avg_latency_ms: float
    avg_cost_usd: float


class PlaygroundCompareRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    primary_model: str
    secondary_model: str
    prompt_template_name: str | None = None
    prompt_template_version: int | None = None


class PlaygroundResult(BaseModel):
    model_name: str
    response: str
    latency_ms: float
    total_tokens: int
    cost_usd: float
    semantic_similarity: float | None = None


class PlaygroundCompareResponse(BaseModel):
    prompt: str
    template: dict[str, Any] | None
    results: list[PlaygroundResult]
