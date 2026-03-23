"""Scoring Agent.

Evaluates overall interview performance with rubric-based
multi-dimensional scoring.
"""

import json
from agents.base_agent import BaseAgent


class ScoringAgent(BaseAgent):
    """Agent that scores the complete interview performance.

    Produces overall, technical, behavioral, communication, and
    problem-solving scores with per-question breakdowns.
    """

    def __init__(self) -> None:
        super().__init__(name="ScoringAgent", prompt_file="scoring.txt")

    async def run(self, state: dict) -> dict:
        """Score the complete interview transcript.

        Args:
            state: Must contain ``transcript``, ``questions``,
                ``jd_analysis``, and ``resume_analysis``.

        Returns:
            The state updated with ``scoring_result`` (dict).
        """
        transcript = state.get("transcript", "[]")
        questions = state.get("questions", "[]")
        jd_analysis = state.get("jd_analysis", "{}")
        resume_analysis = state.get("resume_analysis", "{}")

        # Ensure string format for prompt
        if isinstance(transcript, list):
            transcript = json.dumps(transcript, indent=2)
        if isinstance(questions, list):
            questions = json.dumps(questions, indent=2)
        if isinstance(jd_analysis, dict):
            jd_analysis = json.dumps(jd_analysis, indent=2)
        if isinstance(resume_analysis, dict):
            resume_analysis = json.dumps(resume_analysis, indent=2)

        prompt = self.format_prompt(
            transcript=transcript,
            questions=questions,
            jd_analysis=jd_analysis,
            resume_analysis=resume_analysis,
        )

        response = await self.call_llm(
            prompt,
            system_message="You are an expert interview evaluator. Score fairly and thoroughly. Always respond with valid JSON."
        )
        state["scoring_result"] = self.parse_json_response(response)
        return state

    async def _mock_response(self, prompt: str) -> str:
        """Return mock scoring result data.

        Args:
            prompt: The original prompt (unused).

        Returns:
            JSON string with sample scoring data.
        """
        return json.dumps({
            "overall_score": 74.5,
            "technical_score": 78.0,
            "behavioral_score": 72.0,
            "communication_score": 75.0,
            "problem_solving_score": 73.0,
            "score_breakdown": [
                {"question_index": 0, "question_type": "behavioral", "score": 7, "notes": "Good STAR format, specific example"},
                {"question_index": 1, "question_type": "resume_deep_dive", "score": 8, "notes": "Strong architecture knowledge"},
                {"question_index": 2, "question_type": "technical", "score": 7.5, "notes": "Solid API design understanding"},
                {"question_index": 3, "question_type": "technical", "score": 7, "notes": "Good comparison but lacked depth on CAP theorem"},
                {"question_index": 4, "question_type": "dsa", "score": 8, "notes": "Optimal solution with clean code"},
                {"question_index": 5, "question_type": "system_design", "score": 7, "notes": "Good high-level design, missing cache invalidation strategy"},
                {"question_index": 6, "question_type": "technical", "score": 7.5, "notes": "Systematic debugging approach"},
                {"question_index": 7, "question_type": "behavioral", "score": 7, "notes": "Showed maturity in conflict resolution"}
            ],
            "strengths": [
                "Strong full-stack development fundamentals",
                "Good system design thinking",
                "Clear communication and structured responses",
                "Solid DSA skills"
            ],
            "weaknesses": [
                "Could deepen knowledge of distributed systems",
                "Behavioral answers could be more specific with metrics",
                "Missing discussion of monitoring and observability"
            ],
            "hiring_recommendation": "lean_hire",
            "confidence_level": "medium",
            "grade": "B+"
        })


async def evaluate_answers(state: dict) -> dict:
    """Module-level convenience function for the orchestrator.

    Args:
        state: Pipeline state with transcript and questions.

    Returns:
        Updated state with ``scoring_result``.
    """
    agent = ScoringAgent()
    return await agent.run(state)
