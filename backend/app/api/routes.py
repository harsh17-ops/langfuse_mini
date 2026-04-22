import httpx

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.llm_log import ChatRequest, ChatResponse, DashboardStats, FeedbackRequest, LLMLogRead
from app.services.llm_observer import LLMObserver
from app.services.observability_service import ObservabilityService

router = APIRouter()
llm_observer = LLMObserver()


@router.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
async def create_chat_completion(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    if not llm_observer.groq_client.settings.groq_api_key:
        raise HTTPException(status_code=500, detail="Missing GROQ_API_KEY in backend environment.")

    try:
        return await llm_observer.run_and_log(db, payload.prompt, payload.model_name)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Groq API error: {exc.response.text}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Groq connectivity error: {str(exc)}") from exc


@router.get("/logs", response_model=list[LLMLogRead])
def list_logs(limit: int = 100, db: Session = Depends(get_db)) -> list[LLMLogRead]:
    return ObservabilityService.list_logs(db, limit)


@router.post("/logs/{log_id}/feedback", response_model=LLMLogRead)
def submit_feedback(log_id: int, payload: FeedbackRequest, db: Session = Depends(get_db)) -> LLMLogRead:
    log = ObservabilityService.update_feedback(db, log_id, payload.feedback)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)) -> DashboardStats:
    return DashboardStats(**ObservabilityService.get_stats(db))
