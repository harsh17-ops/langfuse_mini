from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Span(Base):
    __tablename__ = "spans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trace_id: Mapped[int] = mapped_column(ForeignKey("traces.id"), nullable=False, index=True)
    parent_span_id: Mapped[int | None] = mapped_column(ForeignKey("spans.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    trace = relationship("Trace", back_populates="spans")
    parent_span = relationship("Span", remote_side=[id])
    generations = relationship("Generation", back_populates="span", cascade="all, delete-orphan")

