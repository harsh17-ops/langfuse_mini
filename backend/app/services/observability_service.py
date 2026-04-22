from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.llm_log import LLMLog


class ObservabilityService:
    @staticmethod
    def create_log(
        db: Session,
        *,
        prompt: str,
        response: str,
        model_name: str,
        latency_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
    ) -> LLMLog:
        # This table is the core observability record.
        # Each row captures what was sent, what came back, how long it took,
        # and how much usage it consumed.
        log = LLMLog(
            prompt=prompt,
            response=response,
            model_name=model_name,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def list_logs(db: Session, limit: int = 100) -> list[LLMLog]:
        stmt = select(LLMLog).order_by(LLMLog.created_at.desc()).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def update_feedback(db: Session, log_id: int, feedback: str) -> LLMLog | None:
        log = db.get(LLMLog, log_id)
        if not log:
            return None
        log.feedback = feedback
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_stats(db: Session) -> dict:
        total_requests = db.scalar(select(func.count(LLMLog.id))) or 0
        avg_latency_ms = db.scalar(select(func.avg(LLMLog.latency_ms))) or 0
        total_tokens = db.scalar(select(func.sum(LLMLog.total_tokens))) or 0
        positive_feedback = db.scalar(select(func.count()).select_from(LLMLog).where(LLMLog.feedback == "up")) or 0
        negative_feedback = db.scalar(select(func.count()).select_from(LLMLog).where(LLMLog.feedback == "down")) or 0

        return {
            "total_requests": total_requests,
            "avg_latency_ms": round(float(avg_latency_ms), 2),
            "total_tokens": int(total_tokens),
            "positive_feedback": positive_feedback,
            "negative_feedback": negative_feedback,
        }

