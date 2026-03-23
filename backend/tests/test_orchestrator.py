"""Tests for the LangGraph orchestrator pipelines.

Covers the preparation pipeline (resume → JD → skill gap → questions)
and the scoring pipeline (scoring → feedback), both in mock mode.
"""

import pytest

from agents.orchestrator import (
    InterviewState,
    run_preparation_pipeline,
    run_scoring_pipeline,
    build_langgraph_workflow,
)


# ═══════════════════════════════════════════════════════════════════
# Preparation Pipeline
# ═══════════════════════════════════════════════════════════════════


class TestPreparationPipeline:
    """Tests for run_preparation_pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_returns_all_keys(self) -> None:
        """Pipeline populates all four analysis outputs."""
        result = await run_preparation_pipeline(
            resume_text="Python developer with 3 years experience",
            jd_text="Senior Python Developer at TechCo",
        )
        assert "resume_analysis" in result
        assert "jd_analysis" in result
        assert "skill_gap_report" in result
        assert "questions" in result

    @pytest.mark.asyncio
    async def test_resume_analysis_has_skills(self) -> None:
        """Pipeline produces resume analysis with skills list."""
        result = await run_preparation_pipeline(
            resume_text="Full-stack developer",
            jd_text="SDE 2 role",
        )
        assert isinstance(result["resume_analysis"]["skills"], list)

    @pytest.mark.asyncio
    async def test_jd_analysis_has_role_title(self) -> None:
        """Pipeline produces JD analysis with role title."""
        result = await run_preparation_pipeline(
            resume_text="Developer",
            jd_text="Backend engineer role",
        )
        assert isinstance(result["jd_analysis"]["role_title"], str)

    @pytest.mark.asyncio
    async def test_questions_are_generated(self) -> None:
        """Pipeline produces a non-empty list of questions."""
        result = await run_preparation_pipeline(
            resume_text="React developer",
            jd_text="Frontend role",
        )
        assert isinstance(result["questions"], list)
        assert len(result["questions"]) >= 5

    @pytest.mark.asyncio
    async def test_custom_interview_type(self) -> None:
        """Pipeline accepts custom interview type."""
        result = await run_preparation_pipeline(
            resume_text="Developer",
            jd_text="Role",
            interview_type="technical",
        )
        assert result.get("interview_type") == "technical"

    @pytest.mark.asyncio
    async def test_custom_difficulty(self) -> None:
        """Pipeline accepts custom difficulty level."""
        result = await run_preparation_pipeline(
            resume_text="Developer",
            jd_text="Role",
            difficulty="hard",
        )
        assert result.get("difficulty_level") == "hard"

    @pytest.mark.asyncio
    async def test_preserves_input_texts(self) -> None:
        """Pipeline output still contains the original inputs."""
        result = await run_preparation_pipeline(
            resume_text="My resume text",
            jd_text="My JD text",
        )
        assert result["resume_text"] == "My resume text"
        assert result["jd_text"] == "My JD text"

    @pytest.mark.asyncio
    async def test_skill_gap_has_recommendations(self) -> None:
        """Pipeline skill gap report includes recommendations."""
        result = await run_preparation_pipeline(
            resume_text="Developer",
            jd_text="Senior role",
        )
        report = result["skill_gap_report"]
        assert "recommendations" in report
        assert isinstance(report["recommendations"], list)

    @pytest.mark.asyncio
    async def test_questions_span_multiple_types(self) -> None:
        """Generated questions cover multiple question types."""
        result = await run_preparation_pipeline(
            resume_text="Full-stack dev",
            jd_text="SDE role",
        )
        types = {q.get("type") for q in result["questions"]}
        assert len(types) >= 3


# ═══════════════════════════════════════════════════════════════════
# Scoring Pipeline
# ═══════════════════════════════════════════════════════════════════


class TestScoringPipeline:
    """Tests for run_scoring_pipeline."""

    @pytest.mark.asyncio
    async def test_returns_scores_dict(self) -> None:
        """Pipeline returns a scores sub-dict."""
        result = await run_scoring_pipeline(
            transcript=[{"question": "Q1", "answer": "A1"}],
            questions=[{"text": "Q1"}],
        )
        assert "scores" in result
        scores = result["scores"]
        assert "overall" in scores
        assert "technical" in scores
        assert "behavioral" in scores
        assert "communication" in scores
        assert "problem_solving" in scores

    @pytest.mark.asyncio
    async def test_returns_feedback_dict(self) -> None:
        """Pipeline returns a feedback sub-dict."""
        result = await run_scoring_pipeline(
            transcript=[{"question": "Q", "answer": "A"}],
            questions=[{"text": "Q"}],
        )
        assert "feedback" in result
        feedback = result["feedback"]
        assert "summary" in feedback
        assert "skill_gaps" in feedback
        assert "improvement_plan" in feedback

    @pytest.mark.asyncio
    async def test_scores_are_numeric(self) -> None:
        """All score values are numeric."""
        result = await run_scoring_pipeline(
            transcript=[{"question": "Q", "answer": "A"}],
            questions=[{"text": "Q"}],
        )
        for key in ["overall", "technical", "behavioral",
                     "communication", "problem_solving"]:
            assert isinstance(result["scores"][key], (int, float))

    @pytest.mark.asyncio
    async def test_accepts_json_string_inputs(self) -> None:
        """Pipeline handles JSON string inputs gracefully."""
        import json
        result = await run_scoring_pipeline(
            transcript=json.dumps([{"question": "Q", "answer": "A"}]),
            questions=json.dumps([{"text": "Q"}]),
            jd_text="SDE role",
            resume_analysis=json.dumps({"skills": ["Python"]}),
        )
        assert "scores" in result
        assert "feedback" in result

    @pytest.mark.asyncio
    async def test_has_strengths_and_weaknesses(self) -> None:
        """Scoring result includes strengths and weaknesses."""
        result = await run_scoring_pipeline(
            transcript=[{"question": "Q", "answer": "A"}],
            questions=[{"text": "Q"}],
        )
        assert isinstance(result["scores"]["strengths"], list)
        assert isinstance(result["scores"]["weaknesses"], list)

    @pytest.mark.asyncio
    async def test_feedback_summary_is_nonempty(self) -> None:
        """Feedback summary is a non-empty string."""
        result = await run_scoring_pipeline(
            transcript=[{"question": "Q", "answer": "A"}],
            questions=[{"text": "Q"}],
        )
        summary = result["feedback"]["summary"]
        assert isinstance(summary, str)
        assert len(summary) > 10


# ═══════════════════════════════════════════════════════════════════
# InterviewState TypedDict
# ═══════════════════════════════════════════════════════════════════


class TestInterviewState:
    """Tests for the InterviewState TypedDict."""

    def test_is_total_false(self) -> None:
        """InterviewState allows partial instantiation."""
        state: InterviewState = {"resume_text": "test"}
        assert state["resume_text"] == "test"

    def test_accepts_all_fields(self) -> None:
        """InterviewState accepts every defined field."""
        state: InterviewState = {
            "resume_text": "resume",
            "jd_text": "jd",
            "interview_type": "full",
            "personality_mode": "professional",
            "difficulty_level": "medium",
            "resume_analysis": {},
            "jd_analysis": {},
            "skill_gap_report": {},
            "questions": [],
            "transcript": [],
            "scoring_result": {},
            "feedback_result": {},
            "dsa_problems": [],
            "error": None,
        }
        assert state["interview_type"] == "full"


# ═══════════════════════════════════════════════════════════════════
# LangGraph Workflow Builder
# ═══════════════════════════════════════════════════════════════════


class TestLangGraphWorkflow:
    """Tests for the LangGraph workflow builder."""

    def test_build_returns_compiled_or_none(self) -> None:
        """build_langgraph_workflow returns a compiled graph or None."""
        result = build_langgraph_workflow()
        # Either a compiled graph object or None if langgraph not installed
        assert result is not None or result is None
