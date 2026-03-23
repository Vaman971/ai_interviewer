"""Comprehensive tests for all AI agents in mock mode.

Validates each agent's output structure, data types, edge cases,
and error handling. All agents are tested with mock responses
(no API key required).
"""

import json

import pytest

from agents.resume_agent import ResumeAgent, analyze_resume
from agents.jd_agent import JDAgent, analyze_jd
from agents.skill_gap_agent import SkillGapAgent, analyze_skill_gap
from agents.question_agent import QuestionAgent, generate_questions
from agents.scoring_agent import ScoringAgent, evaluate_answers
from agents.feedback_agent import FeedbackAgent, generate_feedback
from agents.interviewer_agent import (
    InterviewerAgent,
    evaluate_single_answer,
)
from agents.dsa_agent import DSAAgent, generate_dsa_problems


# ═══════════════════════════════════════════════════════════════════
# Resume Agent
# ═══════════════════════════════════════════════════════════════════


class TestResumeAgent:
    """Tests for the ResumeAgent."""

    @pytest.mark.asyncio
    async def test_run_returns_structured_analysis(self) -> None:
        """Agent populates resume_analysis with expected keys."""
        agent = ResumeAgent()
        state = {"resume_text": "Experienced Python developer"}
        result = await agent.run(state)

        analysis = result["resume_analysis"]
        assert isinstance(analysis["skills"], list)
        assert len(analysis["skills"]) > 0
        assert isinstance(analysis["experience_years"], (int, float))
        assert isinstance(analysis["experience_summary"], str)
        assert isinstance(analysis["projects"], list)
        assert isinstance(analysis["education"], list)
        assert isinstance(analysis["strengths"], list)

    @pytest.mark.asyncio
    async def test_run_empty_resume_returns_error(self) -> None:
        """Empty resume text produces an error in the analysis."""
        agent = ResumeAgent()
        result = await agent.run({"resume_text": ""})
        assert "error" in result["resume_analysis"]

    @pytest.mark.asyncio
    async def test_run_missing_resume_key(self) -> None:
        """Missing resume_text key produces an error."""
        agent = ResumeAgent()
        result = await agent.run({})
        assert "error" in result["resume_analysis"]

    @pytest.mark.asyncio
    async def test_run_preserves_existing_state(self) -> None:
        """Agent doesn't clobber existing keys in the state dict."""
        agent = ResumeAgent()
        state = {"resume_text": "Python dev", "jd_text": "SDE Role"}
        result = await agent.run(state)
        assert result["jd_text"] == "SDE Role"
        assert "resume_analysis" in result

    @pytest.mark.asyncio
    async def test_module_function_matches_agent(self) -> None:
        """The analyze_resume module function behaves like agent.run."""
        state = {"resume_text": "Full-stack developer"}
        result = await analyze_resume(state)
        assert "resume_analysis" in result
        assert "skills" in result["resume_analysis"]

    @pytest.mark.asyncio
    async def test_mock_has_projects_with_structure(self) -> None:
        """Mock projects have name, description, technologies, impact."""
        agent = ResumeAgent()
        state = {"resume_text": "Developer"}
        result = await agent.run(state)
        projects = result["resume_analysis"]["projects"]
        assert len(projects) > 0
        project = projects[0]
        assert "name" in project
        assert "technologies" in project


# ═══════════════════════════════════════════════════════════════════
# JD Agent
# ═══════════════════════════════════════════════════════════════════


class TestJDAgent:
    """Tests for the JDAgent."""

    @pytest.mark.asyncio
    async def test_run_returns_structured_analysis(self) -> None:
        """Agent populates jd_analysis with expected keys."""
        agent = JDAgent()
        state = {"jd_text": "Looking for Senior Python Developer"}
        result = await agent.run(state)

        analysis = result["jd_analysis"]
        assert isinstance(analysis["role_title"], str)
        assert isinstance(analysis["required_skills"], list)
        assert isinstance(analysis["preferred_skills"], list)
        assert isinstance(analysis["experience_level"], str)
        assert isinstance(analysis["responsibilities"], list)

    @pytest.mark.asyncio
    async def test_run_empty_jd_returns_error(self) -> None:
        """Empty JD text produces an error."""
        agent = JDAgent()
        result = await agent.run({"jd_text": ""})
        assert "error" in result["jd_analysis"]

    @pytest.mark.asyncio
    async def test_run_missing_jd_key(self) -> None:
        """Missing jd_text key produces an error."""
        agent = JDAgent()
        result = await agent.run({})
        assert "error" in result["jd_analysis"]

    @pytest.mark.asyncio
    async def test_module_function(self) -> None:
        """The analyze_jd module function returns jd_analysis."""
        result = await analyze_jd({"jd_text": "SDE2 role"})
        assert "jd_analysis" in result

    @pytest.mark.asyncio
    async def test_required_skills_are_strings(self) -> None:
        """All required skills are strings."""
        agent = JDAgent()
        result = await agent.run({"jd_text": "Backend engineer"})
        for skill in result["jd_analysis"]["required_skills"]:
            assert isinstance(skill, str)


# ═══════════════════════════════════════════════════════════════════
# Skill Gap Agent
# ═══════════════════════════════════════════════════════════════════


class TestSkillGapAgent:
    """Tests for the SkillGapAgent."""

    @pytest.mark.asyncio
    async def test_run_returns_gap_report(self) -> None:
        """Agent produces a structured skill gap report."""
        agent = SkillGapAgent()
        state = {
            "resume_analysis": {"skills": ["Python", "FastAPI"]},
            "jd_analysis": {"required_skills": ["Python", "K8s"]},
        }
        result = await agent.run(state)

        report = result["skill_gap_report"]
        assert isinstance(report["matching_skills"], list)
        assert isinstance(report["missing_skills"], list)
        assert "gap_severity" in report
        assert isinstance(report["recommendations"], list)

    @pytest.mark.asyncio
    async def test_run_missing_inputs_returns_error(self) -> None:
        """Missing analyses produce an error."""
        agent = SkillGapAgent()
        result = await agent.run({})
        assert "error" in result["skill_gap_report"]

    @pytest.mark.asyncio
    async def test_run_empty_analyses_returns_error(self) -> None:
        """Empty analyses produce an error."""
        agent = SkillGapAgent()
        result = await agent.run(
            {"resume_analysis": {}, "jd_analysis": {}}
        )
        assert "error" in result["skill_gap_report"]

    @pytest.mark.asyncio
    async def test_module_function(self) -> None:
        """The analyze_skill_gap function returns skill_gap_report."""
        state = {
            "resume_analysis": {"skills": ["JS"]},
            "jd_analysis": {"required_skills": ["JS", "TS"]},
        }
        result = await analyze_skill_gap(state)
        assert "skill_gap_report" in result

    @pytest.mark.asyncio
    async def test_has_additional_skills(self) -> None:
        """Mock includes additional_skills the candidate has."""
        agent = SkillGapAgent()
        state = {
            "resume_analysis": {"skills": ["Python"]},
            "jd_analysis": {"required_skills": ["Python"]},
        }
        result = await agent.run(state)
        assert "additional_skills" in result["skill_gap_report"]

    @pytest.mark.asyncio
    async def test_gap_severity_is_valid(self) -> None:
        """Gap severity is a reasonable string value."""
        agent = SkillGapAgent()
        state = {
            "resume_analysis": {"skills": ["Python"]},
            "jd_analysis": {"required_skills": ["Python"]},
        }
        result = await agent.run(state)
        severity = result["skill_gap_report"]["gap_severity"]
        assert severity in ("low", "medium", "high", "critical")


# ═══════════════════════════════════════════════════════════════════
# Question Agent
# ═══════════════════════════════════════════════════════════════════


class TestQuestionAgent:
    """Tests for the QuestionAgent."""

    @pytest.mark.asyncio
    async def test_run_returns_list_of_questions(self) -> None:
        """Agent generates a non-empty list of questions."""
        agent = QuestionAgent()
        state = {
            "resume_analysis": {},
            "jd_analysis": {},
            "skill_gap_report": {},
        }
        result = await agent.run(state)
        assert isinstance(result["questions"], list)
        assert len(result["questions"]) >= 5

    @pytest.mark.asyncio
    async def test_questions_have_required_fields(self) -> None:
        """Each question has text, type, difficulty, and category."""
        agent = QuestionAgent()
        state = {
            "resume_analysis": {},
            "jd_analysis": {},
            "skill_gap_report": {},
        }
        result = await agent.run(state)
        for q in result["questions"]:
            assert "text" in q
            assert "type" in q
            assert "difficulty" in q
            assert "category" in q
            assert isinstance(q["text"], str)
            assert len(q["text"]) > 10

    @pytest.mark.asyncio
    async def test_questions_include_multiple_types(self) -> None:
        """Generated questions span multiple types."""
        agent = QuestionAgent()
        state = {
            "resume_analysis": {},
            "jd_analysis": {},
            "skill_gap_report": {},
        }
        result = await agent.run(state)
        types = {q["type"] for q in result["questions"]}
        assert len(types) >= 3  # behavioral, technical, dsa, etc.

    @pytest.mark.asyncio
    async def test_questions_have_expected_answer_points(self) -> None:
        """Each question includes expected answer points."""
        agent = QuestionAgent()
        state = {
            "resume_analysis": {},
            "jd_analysis": {},
            "skill_gap_report": {},
        }
        result = await agent.run(state)
        for q in result["questions"]:
            assert "expected_answer_points" in q
            assert isinstance(q["expected_answer_points"], list)

    @pytest.mark.asyncio
    async def test_module_function(self) -> None:
        """The generate_questions function works like agent.run."""
        state = {
            "resume_analysis": {},
            "jd_analysis": {},
            "skill_gap_report": {},
        }
        result = await generate_questions(state)
        assert "questions" in result

    @pytest.mark.asyncio
    async def test_respects_interview_type(self) -> None:
        """Interview type is forwarded through state."""
        agent = QuestionAgent()
        state = {
            "resume_analysis": {},
            "jd_analysis": {},
            "skill_gap_report": {},
            "interview_type": "technical",
        }
        result = await agent.run(state)
        assert "questions" in result


# ═══════════════════════════════════════════════════════════════════
# Scoring Agent
# ═══════════════════════════════════════════════════════════════════


class TestScoringAgent:
    """Tests for the ScoringAgent."""

    @pytest.mark.asyncio
    async def test_run_returns_all_score_dimensions(self) -> None:
        """Agent returns overall + 4 dimensional scores."""
        agent = ScoringAgent()
        state = {
            "transcript": [{"question": "Q1", "answer": "A1"}],
            "questions": [{"text": "Q1"}],
        }
        result = await agent.run(state)

        scoring = result["scoring_result"]
        assert isinstance(scoring["overall_score"], (int, float))
        assert isinstance(scoring["technical_score"], (int, float))
        assert isinstance(scoring["behavioral_score"], (int, float))
        assert isinstance(scoring["communication_score"], (int, float))
        assert isinstance(scoring["problem_solving_score"], (int, float))

    @pytest.mark.asyncio
    async def test_scores_are_in_valid_range(self) -> None:
        """All scores are between 0 and 100."""
        agent = ScoringAgent()
        state = {
            "transcript": [{"question": "Q", "answer": "A"}],
            "questions": [{"text": "Q"}],
        }
        result = await agent.run(state)
        scoring = result["scoring_result"]

        for key in [
            "overall_score", "technical_score", "behavioral_score",
            "communication_score", "problem_solving_score",
        ]:
            assert 0 <= scoring[key] <= 100

    @pytest.mark.asyncio
    async def test_has_score_breakdown(self) -> None:
        """Scoring result includes per-question breakdown."""
        agent = ScoringAgent()
        state = {
            "transcript": [{"question": "Q", "answer": "A"}],
            "questions": [{"text": "Q"}],
        }
        result = await agent.run(state)
        assert "score_breakdown" in result["scoring_result"]
        assert isinstance(result["scoring_result"]["score_breakdown"], list)

    @pytest.mark.asyncio
    async def test_has_strengths_and_weaknesses(self) -> None:
        """Scoring result includes strengths and weaknesses lists."""
        agent = ScoringAgent()
        state = {
            "transcript": [{"question": "Q", "answer": "A"}],
            "questions": [{"text": "Q"}],
        }
        result = await agent.run(state)
        scoring = result["scoring_result"]
        assert isinstance(scoring["strengths"], list)
        assert isinstance(scoring["weaknesses"], list)
        assert len(scoring["strengths"]) > 0
        assert len(scoring["weaknesses"]) > 0

    @pytest.mark.asyncio
    async def test_handles_list_and_string_inputs(self) -> None:
        """Agent handles both list and JSON string inputs."""
        agent = ScoringAgent()
        state = {
            "transcript": json.dumps([{"question": "Q", "answer": "A"}]),
            "questions": json.dumps([{"text": "Q"}]),
            "jd_analysis": json.dumps({}),
            "resume_analysis": json.dumps({}),
        }
        result = await agent.run(state)
        assert "scoring_result" in result

    @pytest.mark.asyncio
    async def test_module_function(self) -> None:
        """The evaluate_answers function works like agent.run."""
        state = {
            "transcript": [{"question": "Q", "answer": "A"}],
            "questions": [{"text": "Q"}],
        }
        result = await evaluate_answers(state)
        assert "scoring_result" in result


# ═══════════════════════════════════════════════════════════════════
# Feedback Agent
# ═══════════════════════════════════════════════════════════════════


class TestFeedbackAgent:
    """Tests for the FeedbackAgent."""

    @pytest.mark.asyncio
    async def test_run_returns_feedback_structure(self) -> None:
        """Agent produces feedback with summary, areas, and plan."""
        agent = FeedbackAgent()
        state = {"scoring_result": {"overall_score": 75}}
        result = await agent.run(state)

        feedback = result["feedback_result"]
        assert isinstance(feedback["summary"], str)
        assert len(feedback["summary"]) > 50
        assert isinstance(feedback["improvement_areas"], list)
        assert isinstance(feedback["30_day_plan"], str)

    @pytest.mark.asyncio
    async def test_improvement_areas_are_structured(self) -> None:
        """Each improvement area has area, priority, and action_items."""
        agent = FeedbackAgent()
        state = {"scoring_result": {"overall_score": 70}}
        result = await agent.run(state)

        for area in result["feedback_result"]["improvement_areas"]:
            assert "area" in area
            assert "priority" in area
            assert "action_items" in area
            assert isinstance(area["action_items"], list)
            assert area["priority"] in ("low", "medium", "high")

    @pytest.mark.asyncio
    async def test_has_strengths_to_leverage(self) -> None:
        """Feedback includes strengths to leverage."""
        agent = FeedbackAgent()
        state = {"scoring_result": {"overall_score": 80}}
        result = await agent.run(state)
        assert "strengths_to_leverage" in result["feedback_result"]
        assert isinstance(
            result["feedback_result"]["strengths_to_leverage"], list
        )

    @pytest.mark.asyncio
    async def test_has_next_interview_tips(self) -> None:
        """Feedback includes next interview tips."""
        agent = FeedbackAgent()
        state = {"scoring_result": {"overall_score": 65}}
        result = await agent.run(state)
        assert "next_interview_tips" in result["feedback_result"]

    @pytest.mark.asyncio
    async def test_module_function(self) -> None:
        """The generate_feedback function works like agent.run."""
        state = {"scoring_result": {"overall_score": 75}}
        result = await generate_feedback(state)
        assert "feedback_result" in result


# ═══════════════════════════════════════════════════════════════════
# Interviewer Agent
# ═══════════════════════════════════════════════════════════════════


class TestInterviewerAgent:
    """Tests for the InterviewerAgent."""

    @pytest.mark.asyncio
    async def test_evaluate_answer_returns_score(self) -> None:
        """Evaluation includes a numeric score."""
        agent = InterviewerAgent()
        result = await agent.evaluate_answer(
            question_text="Explain REST APIs",
            answer_text="REST uses HTTP methods for CRUD operations",
        )
        assert isinstance(result["score"], (int, float))
        assert 0 <= result["score"] <= 10

    @pytest.mark.asyncio
    async def test_evaluate_answer_returns_feedback(self) -> None:
        """Evaluation includes textual feedback."""
        agent = InterviewerAgent()
        result = await agent.evaluate_answer(
            question_text="What is Docker?",
            answer_text="Docker is a containerisation platform",
        )
        assert isinstance(result["feedback"], str)
        assert len(result["feedback"]) > 10

    @pytest.mark.asyncio
    async def test_evaluate_answer_has_strengths_weaknesses(self) -> None:
        """Evaluation lists strengths and weaknesses."""
        agent = InterviewerAgent()
        result = await agent.evaluate_answer(
            question_text="Q", answer_text="A"
        )
        assert isinstance(result["strengths"], list)
        assert isinstance(result["weaknesses"], list)

    @pytest.mark.asyncio
    async def test_evaluate_answer_with_personality(self) -> None:
        """Custom personality mode is accepted."""
        agent = InterviewerAgent()
        result = await agent.evaluate_answer(
            question_text="Q",
            answer_text="A",
            personality_mode="friendly",
        )
        assert "score" in result

    @pytest.mark.asyncio
    async def test_evaluate_answer_has_follow_up(self) -> None:
        """Evaluation includes a follow-up question."""
        agent = InterviewerAgent()
        result = await agent.evaluate_answer(
            question_text="Q", answer_text="A"
        )
        assert "follow_up" in result
        assert isinstance(result["follow_up"], str)

    @pytest.mark.asyncio
    async def test_run_is_noop(self) -> None:
        """The run method is a no-op (returns state unchanged)."""
        agent = InterviewerAgent()
        state = {"key": "value"}
        result = await agent.run(state)
        assert result == state

    @pytest.mark.asyncio
    async def test_module_function_evaluate(self) -> None:
        """evaluate_single_answer module function works correctly."""
        result = await evaluate_single_answer(
            question_text="What is Python?",
            answer_text="A high-level language",
            jd_context="SDE role",
            personality_mode="professional",
        )
        assert "score" in result
        assert "feedback" in result


# ═══════════════════════════════════════════════════════════════════
# DSA Agent
# ═══════════════════════════════════════════════════════════════════


class TestDSAAgent:
    """Tests for the DSAAgent."""

    @pytest.mark.asyncio
    async def test_run_generates_problem(self) -> None:
        """Agent generates at least one DSA problem."""
        agent = DSAAgent()
        state = {"jd_analysis": {}}
        result = await agent.run(state)

        assert isinstance(result["dsa_problems"], list)
        assert len(result["dsa_problems"]) >= 1

    @pytest.mark.asyncio
    async def test_problem_has_required_fields(self) -> None:
        """Each problem has title, description, examples, constraints."""
        agent = DSAAgent()
        state = {"jd_analysis": {}}
        result = await agent.run(state)

        problem = result["dsa_problems"][0]
        assert "title" in problem
        assert "description" in problem
        assert "examples" in problem
        assert "constraints" in problem
        assert "test_cases" in problem

    @pytest.mark.asyncio
    async def test_problem_has_solution_template(self) -> None:
        """Problem includes a solution template."""
        agent = DSAAgent()
        state = {"jd_analysis": {}}
        result = await agent.run(state)
        problem = result["dsa_problems"][0]
        assert "solution_template" in problem
        assert isinstance(problem["solution_template"], str)

    @pytest.mark.asyncio
    async def test_problem_has_complexity_info(self) -> None:
        """Problem includes time and space complexity."""
        agent = DSAAgent()
        state = {"jd_analysis": {}}
        result = await agent.run(state)
        problem = result["dsa_problems"][0]
        assert "time_complexity" in problem
        assert "space_complexity" in problem

    @pytest.mark.asyncio
    async def test_problem_has_hints(self) -> None:
        """Problem includes hints for the candidate."""
        agent = DSAAgent()
        state = {"jd_analysis": {}}
        result = await agent.run(state)
        problem = result["dsa_problems"][0]
        assert "hints" in problem
        assert isinstance(problem["hints"], list)
        assert len(problem["hints"]) >= 1

    @pytest.mark.asyncio
    async def test_test_cases_are_structured(self) -> None:
        """Test cases have input and expected output."""
        agent = DSAAgent()
        state = {"jd_analysis": {}}
        result = await agent.run(state)
        for tc in result["dsa_problems"][0]["test_cases"]:
            assert "input" in tc
            assert "expected_output" in tc

    @pytest.mark.asyncio
    async def test_module_function(self) -> None:
        """The generate_dsa_problems function works like agent.run."""
        result = await generate_dsa_problems({"jd_analysis": {}})
        assert "dsa_problems" in result

    @pytest.mark.asyncio
    async def test_respects_difficulty_level(self) -> None:
        """Difficulty level is forwarded through state."""
        agent = DSAAgent()
        state = {"jd_analysis": {}, "difficulty_level": "hard"}
        result = await agent.run(state)
        assert "dsa_problems" in result
