"""Interviewer Agent.

Evaluates candidate answers in real-time during the interview,
providing scores, feedback, and follow-up questions.
"""

import json
import logging

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class InterviewerAgent(BaseAgent):
    """Agent that evaluates individual answers during a live interview.

    Provides per-answer scoring, qualitative feedback, strength/weakness
    identification, and optional follow-up questions.
    """

    def __init__(self) -> None:
        super().__init__(name="InterviewerAgent", prompt_file="interview.txt")

    async def run(self, state: dict) -> dict:
        """No-op for pipeline mode — use ``evaluate_answer`` instead.

        Args:
            state: Pipeline state (unused).

        Returns:
            The unmodified state.
        """
        return state

    async def evaluate_answer(
        self,
        question_text: str,
        answer_text: str,
        personality_mode: str = "professional",
        jd_context: str = "",
    ) -> dict:
        """Evaluate a single candidate answer.

        Args:
            question_text: The interview question that was asked.
            answer_text: The candidate's answer.
            personality_mode: Interviewer style for the evaluation tone.
            jd_context: Job description context for relevance scoring.

        Returns:
            Dictionary with ``score``, ``feedback``, ``follow_up``, etc.
        """
        prompt = self.format_prompt(
            current_question=question_text,
            candidate_answer=answer_text,
            personality_mode=personality_mode,
        )

        response = await self.call_llm(
            prompt,
            system_message=(
                f"You are a {personality_mode} technical interviewer. "
                "Evaluate the answer fairly. Always respond with valid JSON."
            ),
        )
        return self.parse_json_response(response)

    async def _mock_response(self, prompt: str) -> str:
        """Return mock answer evaluation data.

        Args:
            prompt: The original prompt (unused).

        Returns:
            JSON string with sample evaluation.
        """
        return json.dumps({
            "score": 7.5,
            "feedback": (
                "Good answer demonstrating solid understanding. "
                "Could be improved with more specific examples."
            ),
            "strengths": [
                "Clear explanation",
                "Good use of technical terminology",
                "Structured response",
            ],
            "weaknesses": [
                "Could include more concrete examples",
                "Missing edge case discussion",
            ],
            "follow_up": (
                "Can you elaborate on how you would handle "
                "the edge case where the input is empty?"
            ),
            "should_move_on": True,
            "encouragement": "Great job! You clearly have a strong foundation here.",
        })


async def evaluate_single_answer(
    question_text: str,
    answer_text: str,
    jd_context: str = "",
    personality_mode: str = "professional",
) -> dict:
    """Evaluate a single answer — convenience function for API routes.

    Args:
        question_text: The interview question.
        answer_text: The candidate's answer.
        jd_context: Job description context.
        personality_mode: Interviewer personality style.

    Returns:
        Dictionary with ``score``, ``feedback``, and ``follow_up``.
    """
    agent = InterviewerAgent()
    return await agent.evaluate_answer(
        question_text=question_text,
        answer_text=answer_text,
        personality_mode=personality_mode,
        jd_context=jd_context,
    )
