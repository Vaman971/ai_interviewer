"""Pydantic v2 schemas for Result-related responses."""

from datetime import datetime

from pydantic import BaseModel


class ResultResponse(BaseModel):
    """Response schema for interview results.

    Attributes:
        id: Result UUID.
        interview_id: Parent interview UUID.
        overall_score: Aggregate score (0-100).
        technical_score: Technical assessment score.
        behavioral_score: Behavioral assessment score.
        communication_score: Communication assessment score.
        problem_solving_score: Problem-solving assessment score.
        feedback: Detailed feedback summary (JSON string).
        skill_gaps: Identified skill gaps (JSON string).
        improvement_plan: 30-day improvement plan (JSON string).
        strengths: Candidate strengths (JSON string).
        weaknesses: Areas for improvement (JSON string).
        total_questions: Total questions in the interview.
        questions_answered: Number of questions answered.
        created_at: Result creation timestamp.
    """

    id: str
    interview_id: str
    overall_score: float | None
    technical_score: float | None
    behavioral_score: float | None
    communication_score: float | None
    problem_solving_score: float | None
    feedback: str | None
    skill_gaps: str | None
    improvement_plan: str | None
    strengths: str | None
    weaknesses: str | None
    total_questions: int | None
    questions_answered: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScoreSummary(BaseModel):
    """Compact score summary for display.

    Attributes:
        overall_score: Aggregate score (0-100).
        technical_score: Technical score.
        behavioral_score: Behavioral score.
        communication_score: Communication score.
        problem_solving_score: Problem-solving score.
        grade: Letter grade (A+, A, B+, etc.).
        percentile: Estimated percentile (e.g. 'Top 20%').
    """

    overall_score: float
    technical_score: float
    behavioral_score: float
    communication_score: float
    problem_solving_score: float
    grade: str
    percentile: str
