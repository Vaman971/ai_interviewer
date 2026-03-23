"""Pydantic v2 schemas for Interview-related requests and responses."""

from datetime import datetime

from pydantic import BaseModel


class InterviewCreate(BaseModel):
    """Request schema for creating a new interview session.

    Attributes:
        jd_text: Optional pre-filled job description text.
        interview_type: Type of interview (full, technical, behavioral, dsa).
        personality_mode: Interviewer personality setting.
        difficulty_level: Question difficulty (easy, medium, hard).
    """

    jd_text: str | None = None
    interview_type: str = "full"
    personality_mode: str = "professional"
    difficulty_level: str = "medium"


class SubmitAnswer(BaseModel):
    """Request schema for submitting a candidate answer.

    Attributes:
        question_index: Zero-based index of the question being answered.
        answer_text: The candidate's textual answer.
        time_taken_seconds: Optional time the candidate spent answering.
        warnings: Optional list of cheat warnings (e.g. "Tab switched", "Pasted text").
    """

    question_index: int
    answer_text: str
    time_taken_seconds: float | None = None
    warnings: list[str] = []


class InterviewResponse(BaseModel):
    """Response schema for interview session data.

    Attributes:
        id: Interview UUID.
        user_id: Owning user UUID.
        jd_text: Job description text.
        resume_filename: Uploaded resume filename.
        status: Current lifecycle status.
        interview_type: Type of interview round.
        personality_mode: Interviewer personality setting.
        difficulty_level: Question difficulty level.
        current_question_index: Index of the next question.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    id: str
    user_id: str
    jd_text: str | None
    resume_filename: str | None
    status: str
    interview_type: str
    personality_mode: str
    difficulty_level: str
    current_question_index: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InterviewListResponse(BaseModel):
    """Paginated list of interviews.

    Attributes:
        interviews: List of interview summaries.
        total: Total count for pagination.
    """

    interviews: list[InterviewResponse]
    total: int


class QuestionResponse(BaseModel):
    """Response schema for a single interview question.

    Attributes:
        question_index: Zero-based question position.
        question_text: The question text to present.
        question_type: Category (behavioral, technical, dsa, etc.).
        difficulty: Question difficulty level.
        total_questions: Total questions in the interview.
    """

    question_index: int
    question_text: str
    question_type: str
    difficulty: str
    total_questions: int


class AnswerEvaluation(BaseModel):
    """Response schema for an evaluated answer.

    Attributes:
        question_index: Corresponding question index.
        score: Numeric score (0.0-10.0).
        feedback: Textual evaluation feedback.
        follow_up: Optional follow-up question.
    """

    question_index: int
    score: float
    feedback: str
    follow_up: str | None = None


class ResumeAnalysis(BaseModel):
    """Structured resume analysis output.

    Attributes:
        skills: List of extracted skills.
        experience_years: Total years of experience.
        experience_summary: Brief experience overview.
        projects: List of project details.
        education: List of education entries.
        strengths: Key professional strengths.
    """

    skills: list[str]
    experience_years: float
    experience_summary: str
    projects: list[dict]
    education: list[dict]
    strengths: list[str]


class JDAnalysis(BaseModel):
    """Structured job description analysis output.

    Attributes:
        role_title: Extracted role title.
        required_skills: Must-have skills.
        preferred_skills: Nice-to-have skills.
        experience_level: Seniority level.
        responsibilities: Key job responsibilities.
    """

    role_title: str
    required_skills: list[str]
    preferred_skills: list[str]
    experience_level: str
    responsibilities: list[str]


class SkillGapReport(BaseModel):
    """Skill gap analysis between candidate and role.

    Attributes:
        matching_skills: Skills the candidate already has.
        missing_skills: Required skills the candidate lacks.
        additional_skills: Candidate skills not in the JD.
        gap_severity: Overall gap severity level.
        recommendations: Preparation recommendations.
    """

    matching_skills: list[str]
    missing_skills: list[str]
    additional_skills: list[str]
    gap_severity: str
    recommendations: list[str]
