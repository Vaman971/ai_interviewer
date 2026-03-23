"""SQLAlchemy ORM model for the Result entity."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base

if TYPE_CHECKING:
    from backend.app.models.interview import Interview


def _utcnow() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class Result(Base):
    """Scoring and feedback results for a completed interview.

    Attributes:
        id: UUID primary key.
        interview_id: Foreign key to the parent interview.
        overall_score: Aggregate score (0-100).
        technical_score: Technical skills score (0-100).
        behavioral_score: Behavioral assessment score (0-100).
        communication_score: Communication clarity score (0-100).
        problem_solving_score: Problem-solving ability score (0-100).
        score_breakdown: JSON-serialised per-question scores.
        feedback: JSON-serialised detailed feedback summary.
        skill_gaps: JSON-serialised list of skill gaps.
        improvement_plan: JSON-serialised 30-day improvement plan.
        strengths: JSON-serialised list of strengths.
        weaknesses: JSON-serialised list of weaknesses.
        cheating_flags: JSON-serialised list of cheat detection warnings.
        total_questions: Number of questions in the interview.
        questions_answered: Number of questions the candidate answered.
    """

    __tablename__ = "results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    interview_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("interviews.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Scores
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    technical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    behavioral_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    communication_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    problem_solving_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # Detailed data (stored as JSON strings)
    score_breakdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    skill_gaps: Mapped[str | None] = mapped_column(Text, nullable=True)
    improvement_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    weaknesses: Mapped[str | None] = mapped_column(Text, nullable=True)
    cheating_flags: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    total_questions: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    questions_answered: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Relationships
    interview: Mapped[Interview] = relationship(
        "Interview", back_populates="result"
    )

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return (
            f"<Result interview={self.interview_id} "
            f"score={self.overall_score}>"
        )
