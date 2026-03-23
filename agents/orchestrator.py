"""LangGraph Orchestrator.

Wires all agents into a pipeline for the AI interview workflow.
Provides two main pipelines:

1. **Preparation**: resume → jd → skill_gap → questions
2. **Scoring**: evaluate answers → generate feedback
"""

import json
import logging
from typing import Any, TypedDict

from agents.resume_agent import analyze_resume
from agents.jd_agent import analyze_jd
from agents.skill_gap_agent import analyze_skill_gap
from agents.question_agent import generate_questions
from agents.scoring_agent import evaluate_answers
from agents.feedback_agent import generate_feedback

logger = logging.getLogger(__name__)


class InterviewState(TypedDict, total=False):
    """Shared state flowing through the agent pipeline."""

    # Inputs
    resume_text: str
    jd_text: str
    interview_type: str
    personality_mode: str
    difficulty_level: str

    # Agent outputs
    resume_analysis: dict
    jd_analysis: dict
    skill_gap_report: dict
    questions: list
    transcript: list
    scoring_result: dict
    feedback_result: dict
    dsa_problems: list

    # Metadata
    error: str | None


async def run_preparation_pipeline(
    resume_text: str,
    jd_text: str,
    interview_type: str = "full",
    personality_mode: str = "professional",
    difficulty: str = "medium",
) -> dict:
    """Run the interview preparation pipeline.

    Executes sequentially: Resume Analysis → JD Analysis →
    Skill Gap Detection → Question Generation.

    Args:
        resume_text: Extracted text from the candidate's resume.
        jd_text: Job description text.
        interview_type: Type of interview (full, technical, behavioral, dsa).
        personality_mode: Interviewer personality setting.
        difficulty: Question difficulty level.

    Returns:
        The complete pipeline state with all analysis results.

    Raises:
        RuntimeError: If any pipeline step fails.
    """
    state: dict[str, Any] = {
        "resume_text": resume_text,
        "jd_text": jd_text,
        "interview_type": interview_type,
        "personality_mode": personality_mode,
        "difficulty_level": difficulty,
    }

    try:
        logger.info("Step 1/4: Analyzing resume")
        state = await analyze_resume(state)

        logger.info("Step 2/4: Analyzing job description")
        state = await analyze_jd(state)

        logger.info("Step 3/4: Identifying skill gaps")
        state = await analyze_skill_gap(state)

        logger.info("Step 4/4: Generating questions")
        state = await generate_questions(state)

    except Exception as exc:
        state["error"] = str(exc)
        logger.exception("Preparation pipeline failed at step: %s", exc)
        raise

    return state


async def run_scoring_pipeline(
    transcript: list | str,
    questions: list | str,
    jd_text: str = "",
    resume_analysis: dict | str | None = None,
) -> dict:
    """Run the scoring and feedback pipeline.

    Executes sequentially: Scoring → Feedback Generation.

    Args:
        transcript: List of Q/A pairs (or JSON string).
        questions: List of questions (or JSON string).
        jd_text: Job description text for context.
        resume_analysis: Parsed resume analysis (or JSON string).

    Returns:
        Dictionary with ``scores`` and ``feedback`` sub-dicts.
    """
    state: dict[str, Any] = {
        "transcript": (
            json.loads(transcript) if isinstance(transcript, str) else transcript
        ),
        "questions": (
            json.loads(questions) if isinstance(questions, str) else questions
        ),
        "jd_text": jd_text,
        "resume_analysis": (
            json.loads(resume_analysis)
            if isinstance(resume_analysis, str)
            else (resume_analysis or {})
        ),
    }

    try:
        logger.info("Step 1/2: Scoring interview")
        state = await evaluate_answers(state)

        logger.info("Step 2/2: Generating feedback")
        state = await generate_feedback(state)

    except Exception as exc:
        state["error"] = str(exc)
        logger.exception("Scoring pipeline failed: %s", exc)
        raise

    scoring = state.get("scoring_result", {})
    feedback_data = state.get("feedback_result", {})

    return {
        "scores": {
            "overall": scoring.get("overall_score", 50),
            "technical": scoring.get("technical_score", 50),
            "behavioral": scoring.get("behavioral_score", 50),
            "communication": scoring.get("communication_score", 50),
            "problem_solving": scoring.get("problem_solving_score", 50),
            "strengths": scoring.get("strengths", []),
            "weaknesses": scoring.get("weaknesses", []),
            "breakdown": scoring.get("score_breakdown", []),
        },
        "feedback": {
            "summary": feedback_data.get("summary", ""),
            "skill_gaps": feedback_data.get("improvement_areas", []),
            "improvement_plan": feedback_data.get("30_day_plan", ""),
        },
    }


def build_langgraph_workflow() -> Any:
    """Build a LangGraph StateGraph for advanced pipeline usage.

    Returns:
        The compiled LangGraph workflow, or ``None`` if LangGraph
        is not installed.
    """
    try:
        from langgraph.graph import StateGraph

        graph = StateGraph(InterviewState)

        graph.add_node("resume", analyze_resume)
        graph.add_node("jd", analyze_jd)
        graph.add_node("skill_gap", analyze_skill_gap)
        graph.add_node("questions", generate_questions)
        graph.add_node("score", evaluate_answers)
        graph.add_node("feedback", generate_feedback)

        graph.set_entry_point("resume")
        graph.add_edge("resume", "jd")
        graph.add_edge("jd", "skill_gap")
        graph.add_edge("skill_gap", "questions")
        graph.add_edge("questions", "score")
        graph.add_edge("score", "feedback")
        graph.set_finish_point("feedback")

        return graph.compile()

    except ImportError:
        logger.warning("LangGraph not installed — using direct pipeline functions")
        return None
