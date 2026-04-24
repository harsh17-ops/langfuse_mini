from collections.abc import Iterable
from statistics import quantiles

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.generation import Generation
from app.models.prompt_template import PromptTemplate
from app.models.score import Score
from app.models.span import Span
from app.models.trace import Trace
from app.schemas.observability import TraceSummary


class ObservabilityService:
    @staticmethod
    def create_trace(db: Session, *, name: str, input: str, session_id: str | None, user_id: str | None) -> Trace:
        trace = Trace(name=name, input=input, session_id=session_id, user_id=user_id, status="success")
        db.add(trace)
        db.flush()
        return trace

    @staticmethod
    def create_span(
        db: Session,
        *,
        trace_id: int,
        name: str,
        type: str,
        latency_ms: float = 0.0,
        parent_span_id: int | None = None,
        metadata_json: str | None = None,
        status: str = "success",
    ) -> Span:
        span = Span(
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=name,
            type=type,
            latency_ms=latency_ms,
            metadata_json=metadata_json,
            status=status,
        )
        db.add(span)
        db.flush()
        return span

    @staticmethod
    def create_generation(
        db: Session,
        *,
        span_id: int,
        model: str,
        prompt: str,
        response: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        latency_ms: float,
        cost_usd: float,
        prompt_template_name: str | None = None,
        prompt_template_version: int | None = None,
        status: str = "success",
        error_message: str | None = None,
    ) -> Generation:
        generation = Generation(
            span_id=span_id,
            model=model,
            prompt=prompt,
            response=response,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            prompt_template_name=prompt_template_name,
            prompt_template_version=prompt_template_version,
            status=status,
            error_message=error_message,
        )
        db.add(generation)
        db.flush()
        return generation

    @staticmethod
    def create_score(
        db: Session,
        *,
        trace_id: int,
        generation_id: int | None,
        name: str,
        value: float | bool | str,
        data_type: str,
        source: str,
    ) -> Score:
        score = Score(
            trace_id=trace_id,
            generation_id=generation_id,
            name=name,
            data_type=data_type,
            source=source,
            value_numeric=float(value) if data_type == "NUMERIC" else None,
            value_boolean=bool(value) if data_type == "BOOLEAN" else None,
            value_categorical=str(value) if data_type == "CATEGORICAL" else None,
        )
        db.add(score)
        db.flush()
        return score

    @staticmethod
    def finalize_trace(db: Session, *, trace: Trace, output: str, status: str, generation: Generation, span: Span) -> None:
        trace.output = output
        trace.status = status
        span.latency_ms = generation.latency_ms
        span.status = status
        db.commit()
        db.refresh(trace)

    @staticmethod
    def list_traces(db: Session, limit: int = 50, search: str | None = None) -> list[TraceSummary]:
        stmt = (
            select(Trace)
            .options(selectinload(Trace.spans).selectinload(Span.generations), selectinload(Trace.scores))
            .order_by(Trace.created_at.desc())
            .limit(limit)
        )
        if search:
            stmt = stmt.where(Trace.input.ilike(f"%{search}%") | Trace.name.ilike(f"%{search}%"))

        traces = list(db.scalars(stmt).all())
        return [ObservabilityService._to_summary(trace) for trace in traces]

    @staticmethod
    def get_trace(db: Session, trace_id: int) -> Trace | None:
        stmt = (
            select(Trace)
            .where(Trace.id == trace_id)
            .options(selectinload(Trace.spans).selectinload(Span.generations), selectinload(Trace.scores))
        )
        return db.scalar(stmt)

    @staticmethod
    def filter_traces_by_score(db: Session, score_name: str, min_value: float | None = None) -> list[TraceSummary]:
        stmt = (
            select(Trace)
            .join(Score, Score.trace_id == Trace.id)
            .options(selectinload(Trace.spans).selectinload(Span.generations), selectinload(Trace.scores))
            .where(Score.name == score_name)
            .order_by(Trace.created_at.desc())
        )
        if min_value is not None:
            stmt = stmt.where(Score.value_numeric >= min_value)
        traces = list(db.scalars(stmt).unique().all())
        return [ObservabilityService._to_summary(trace) for trace in traces]

    @staticmethod
    def list_scores(db: Session, trace_id: int | None = None) -> list[Score]:
        stmt = select(Score).order_by(Score.created_at.desc())
        if trace_id is not None:
            stmt = stmt.where(Score.trace_id == trace_id)
        return list(db.scalars(stmt).all())

    @staticmethod
    def submit_feedback(db: Session, trace_id: int, feedback: str) -> Trace | None:
        trace = db.get(Trace, trace_id)
        if not trace:
            return None

        existing = db.scalar(
            select(Score).where(Score.trace_id == trace_id, Score.name == "human_feedback", Score.source == "human")
        )
        if existing:
            existing.value_categorical = feedback
        else:
            ObservabilityService.create_score(
                db,
                trace_id=trace_id,
                generation_id=None,
                name="human_feedback",
                value=feedback,
                data_type="CATEGORICAL",
                source="human",
            )
        db.commit()
        return ObservabilityService.get_trace(db, trace_id)

    @staticmethod
    def get_dashboard_stats(db: Session) -> dict:
        total_traces = db.scalar(select(func.count(Trace.id))) or 0
        avg_latency_ms = db.scalar(select(func.avg(Generation.latency_ms))) or 0
        total_tokens = db.scalar(select(func.sum(Generation.total_tokens))) or 0
        total_cost_usd = db.scalar(select(func.sum(Generation.cost_usd))) or 0

        latencies = list(db.scalars(select(Generation.latency_ms)).all())
        p95_latency_ms = round(ObservabilityService._percentile(latencies, 0.95), 2) if latencies else 0.0

        positive_feedback = (
            db.scalar(
                select(func.count())
                .select_from(Score)
                .where(Score.name == "human_feedback", Score.value_categorical == "up")
            )
            or 0
        )
        negative_feedback = (
            db.scalar(
                select(func.count())
                .select_from(Score)
                .where(Score.name == "human_feedback", Score.value_categorical == "down")
            )
            or 0
        )
        avg_overall_score = (
            db.scalar(select(func.avg(Score.value_numeric)).where(Score.name == "overall", Score.source == "llm_judge"))
            or 0
        )
        avg_semantic_similarity = db.scalar(select(func.avg(Score.value_numeric)).where(Score.name == "semantic_similarity")) or 0
        avg_grounded_overlap = db.scalar(select(func.avg(Score.value_numeric)).where(Score.name == "grounded_overlap")) or 0
        retrieval_trace_count = (
            db.scalar(
                select(func.count(func.distinct(Trace.id)))
                .select_from(Trace)
                .join(Span, Span.trace_id == Trace.id)
                .where(Span.type == "RETRIEVAL")
            )
            or 0
        )

        return {
            "total_traces": total_traces,
            "avg_latency_ms": round(float(avg_latency_ms), 2),
            "p95_latency_ms": p95_latency_ms,
            "total_tokens": int(total_tokens or 0),
            "total_cost_usd": round(float(total_cost_usd or 0), 6),
            "positive_feedback": positive_feedback,
            "negative_feedback": negative_feedback,
            "avg_overall_score": round(float(avg_overall_score), 4),
            "avg_semantic_similarity": round(float(avg_semantic_similarity), 4),
            "avg_grounded_overlap": round(float(avg_grounded_overlap), 4),
            "retrieval_trace_count": retrieval_trace_count,
        }

    @staticmethod
    def get_analytics_overview(db: Session) -> dict:
        model_usage_rows = list(
            db.execute(
                select(Generation.model, func.count(Generation.id))
                .group_by(Generation.model)
                .order_by(func.count(Generation.id).desc())
            ).all()
        )

        score_distributions = []
        for score_name in ["semantic_similarity", "grounded_overlap", "hallucinated", "off-topic", "overall"]:
            average = db.scalar(select(func.avg(Score.value_numeric)).where(Score.name == score_name)) or 0
            score_distributions.append({"score_name": score_name, "average": round(float(average), 4)})

        return {
            "stats": ObservabilityService.get_dashboard_stats(db),
            "model_usage": [{"model_name": model_name, "trace_count": count} for model_name, count in model_usage_rows],
            "score_distributions": score_distributions,
        }

    @staticmethod
    def list_prompt_templates(db: Session) -> list[PromptTemplate]:
        stmt = select(PromptTemplate).order_by(PromptTemplate.name.asc(), PromptTemplate.version.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def create_prompt_template(db: Session, *, name: str, content: str, label: str = "staging") -> PromptTemplate:
        existing_versions = list(
            db.scalars(select(PromptTemplate.version).where(PromptTemplate.name == name).order_by(PromptTemplate.version.desc())).all()
        )
        next_version = (existing_versions[0] + 1) if existing_versions else 1
        if label == "production":
            db.query(PromptTemplate).filter(PromptTemplate.name == name, PromptTemplate.label == "production").update({"label": "staging"})
        prompt_template = PromptTemplate(name=name, version=next_version, content=content, label=label)
        db.add(prompt_template)
        db.commit()
        db.refresh(prompt_template)
        return prompt_template

    @staticmethod
    def promote_prompt_label(db: Session, *, name: str, version: int, label: str) -> PromptTemplate | None:
        prompt_template = db.scalar(select(PromptTemplate).where(PromptTemplate.name == name, PromptTemplate.version == version))
        if not prompt_template:
            return None
        if label == "production":
            db.query(PromptTemplate).filter(PromptTemplate.name == name, PromptTemplate.label == "production").update({"label": "staging"})
        prompt_template.label = label
        db.commit()
        db.refresh(prompt_template)
        return prompt_template

    @staticmethod
    def get_prompt_by_label(db: Session, *, name: str, label: str = "production") -> PromptTemplate | None:
        stmt = (
            select(PromptTemplate)
            .where(PromptTemplate.name == name, PromptTemplate.label == label)
            .order_by(PromptTemplate.version.desc())
        )
        return db.scalar(stmt)

    @staticmethod
    def get_prompt_template(db: Session, *, name: str, version: int | None) -> PromptTemplate | None:
        stmt = select(PromptTemplate).where(PromptTemplate.name == name)
        if version is not None:
            stmt = stmt.where(PromptTemplate.version == version)
        else:
            stmt = stmt.order_by(PromptTemplate.version.desc())
        return db.scalar(stmt)

    @staticmethod
    def get_prompt_metrics(db: Session, *, name: str) -> list[dict]:
        templates = list(db.scalars(select(PromptTemplate).where(PromptTemplate.name == name).order_by(PromptTemplate.version.asc())).all())
        metrics: list[dict] = []
        for template in templates:
            stmt = select(Generation).where(
                Generation.prompt_template_name == template.name,
                Generation.prompt_template_version == template.version,
            )
            generations = list(db.scalars(stmt).all())
            generation_ids = [generation.id for generation in generations]
            avg_overall_score = 0.0
            if generation_ids:
                avg_overall_score = float(
                    db.scalar(
                        select(func.avg(Score.value_numeric)).where(
                            Score.generation_id.in_(generation_ids), Score.name == "overall", Score.source == "llm_judge"
                        )
                    )
                    or 0
                )
            avg_latency_ms = sum(g.latency_ms for g in generations) / len(generations) if generations else 0.0
            avg_cost_usd = sum(g.cost_usd for g in generations) / len(generations) if generations else 0.0
            metrics.append(
                {
                    "version": template.version,
                    "label": template.label,
                    "generations": len(generations),
                    "avg_overall_score": round(avg_overall_score, 4),
                    "avg_latency_ms": round(avg_latency_ms, 2),
                    "avg_cost_usd": round(avg_cost_usd, 6),
                }
            )
        return metrics

    @staticmethod
    def _to_summary(trace: Trace) -> TraceSummary:
        generations = [generation for span in trace.spans for generation in span.generations]
        latest_generation = max(generations, key=lambda generation: generation.created_at) if generations else None
        overall_score = ObservabilityService._find_numeric_score(trace.scores, "overall")
        semantic_similarity = ObservabilityService._find_numeric_score(trace.scores, "semantic_similarity")
        grounded_overlap = ObservabilityService._find_numeric_score(trace.scores, "grounded_overlap")
        human_feedback = ObservabilityService._find_categorical_score(trace.scores, "human_feedback")
        retrieval_used = any(span.type == "RETRIEVAL" for span in trace.spans)
        prompt_family = latest_generation.prompt_template_name if latest_generation else None

        return TraceSummary(
            id=trace.id,
            name=trace.name,
            session_id=trace.session_id,
            user_id=trace.user_id,
            input=trace.input,
            output=trace.output,
            status=trace.status,
            created_at=trace.created_at,
            latest_generation_model=latest_generation.model if latest_generation else None,
            latest_generation_latency_ms=latest_generation.latency_ms if latest_generation else None,
            latest_generation_total_tokens=latest_generation.total_tokens if latest_generation else None,
            overall_score=overall_score,
            semantic_similarity=semantic_similarity,
            grounded_overlap=grounded_overlap,
            human_feedback=human_feedback,
            retrieval_used=retrieval_used,
            prompt_family=prompt_family,
        )

    @staticmethod
    def _find_numeric_score(scores: Iterable[Score], name: str) -> float | None:
        for score in scores:
            if score.name == name and score.value_numeric is not None:
                return score.value_numeric
        return None

    @staticmethod
    def _find_categorical_score(scores: Iterable[Score], name: str) -> str | None:
        for score in scores:
            if score.name == name and score.value_categorical is not None:
                return score.value_categorical
        return None

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float:
        if len(values) == 1:
            return values[0]
        cutoffs = quantiles(sorted(values), n=100)
        index = max(0, min(98, int(percentile * 100) - 1))
        return cutoffs[index]
