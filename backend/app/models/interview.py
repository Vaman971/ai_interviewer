"""SQLAlchemy ORM model for the Interview entity."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.database import Base

if TYPE_CHECKING:
    from backend.app.models.result import Result
    from backend.app.models.user import User


def _utcnow() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class InterviewStatus(str, PyEnum):
    """Lifecycle states for an interview session."""

    CREATED = "created"
    ANALYZING = "analyzing"
    QUESTIONS_READY = "questions_ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SCORED = "scored"
    FAILED = "failed"


class InterviewType(str, PyEnum):
    """Supported interview round types."""

    FULL = "full"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    DSA = "dsa"
    SYSTEM_DESIGN = "system_design"


class Interview(Base):
    """A single interview session between a candidate and the AI.

    Attributes:
        id: UUID primary key.
        user_id: Foreign key to the owning user.
        jd_text: Raw job description text.
        resume_text: Extracted text from the uploaded resume.
        resume_filename: Original filename of the uploaded resume.
        status: Current lifecycle status.
        interview_type: Type of interview round.
        resume_analysis: JSON-serialised resume analysis.
        jd_analysis: JSON-serialised JD analysis.
        skill_gap_report: JSON-serialised skill gap report.
        questions: JSON-serialised list of generated questions.
        transcript: JSON-serialised list of Q/A pairs.
        personality_mode: Interviewer personality setting.
        difficulty_level: Difficulty of the questions.
        current_question_index: Index of the current question.
    """

    __tablename__ = "interviews"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    jd_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_filename: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(50), default=InterviewStatus.CREATED.value
    )
    interview_type: Mapped[str] = mapped_column(
        String(50), default=InterviewType.FULL.value
    )

    # AI-generated data (stored as JSON strings)
    resume_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    jd_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    skill_gap_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    questions: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Interview settings
    personality_mode: Mapped[str] = mapped_column(
        String(50), default="professional"
    )
    difficulty_level: Mapped[str] = mapped_column(
        String(50), default="medium"
    )
    current_question_index: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="interviews")
    result: Mapped[Result | None] = relationship(
        "Result",
        back_populates="interview",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return f"<Interview {self.id} status={self.status}>"
