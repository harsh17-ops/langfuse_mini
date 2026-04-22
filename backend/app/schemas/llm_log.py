from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt sent by the user to the LLM.")
    model_name: str | None = Field(default=None, description="Optional per-request model override.")


class ChatResponse(BaseModel):
    log_id: int
    response: str
    model_name: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMLogRead(BaseModel):
    id: int
    prompt: str
    response: str
    model_name: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    feedback: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackRequest(BaseModel):
    feedback: Literal["up", "down"]


class DashboardStats(BaseModel):
    total_requests: int
    avg_latency_ms: float
    total_tokens: int
    positive_feedback: int
    negative_feedback: int

