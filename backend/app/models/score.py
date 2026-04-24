from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trace_id: Mapped[int] = mapped_column(ForeignKey("traces.id"), nullable=False, index=True)
    generation_id: Mapped[int | None] = mapped_column(ForeignKey("generations.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_boolean: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    value_categorical: Mapped[str | None] = mapped_column(String(120), nullable=True)
    data_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    trace = relationship("Trace", back_populates="scores")
    generation = relationship("Generation", back_populates="scores")

