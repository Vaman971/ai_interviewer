"""Feedback Agent.

Generates detailed improvement plans based on interview performance,
including prioritised action items, resources, and a 30-day plan.
"""

import json
from agents.base_agent import BaseAgent


class FeedbackAgent(BaseAgent):
    """Agent that generates actionable improvement plans.

    Uses scoring results, resume analysis, JD analysis, and skill
    gap data to create a personalised 30-day preparation plan.
    """

    def __init__(self) -> None:
        super().__init__(name="FeedbackAgent", prompt_file="feedback.txt")

    async def run(self, state: dict) -> dict:
        """Generate an improvement plan from scoring results.

        Args:
            state: Must contain ``scoring_result``, ``resume_analysis``,
                ``jd_analysis``, and ``skill_gap_report``.

        Returns:
            The state updated with ``feedback_result`` (dict).
        """
        scoring_result = state.get("scoring_result", {})
        resume_analysis = state.get("resume_analysis", {})
        jd_analysis = state.get("jd_analysis", {})
        skill_gap_report = state.get("skill_gap_report", {})

        prompt = self.format_prompt(
            scoring_result=json.dumps(scoring_result, indent=2),
            resume_analysis=json.dumps(resume_analysis, indent=2),
            jd_analysis=json.dumps(jd_analysis, indent=2),
            skill_gap_report=json.dumps(skill_gap_report, indent=2),
        )

        response = await self.call_llm(
            prompt,
            system_message="You are an expert career coach. Generate actionable improvement plans. Always respond with valid JSON."
        )
        state["feedback_result"] = self.parse_json_response(response)
        return state

    async def _mock_response(self, prompt: str) -> str:
        """Return mock feedback data.

        Args:
            prompt: The original prompt (unused).

        Returns:
            JSON string with sample improvement plan.
        """
        return json.dumps({
            "summary": "You demonstrated solid full-stack development skills with a grade of B+. Your technical fundamentals are strong, particularly in API design and system architecture. The main areas for improvement are distributed systems knowledge and providing more specific metrics in behavioral answers. With focused preparation in the areas outlined below, you'll be well-positioned for senior roles at top companies.",
            "improvement_areas": [
                {
                    "area": "Distributed Systems",
                    "current_level": "intermediate",
                    "target_level": "advanced",
                    "priority": "high",
                    "action_items": [
                        "Study CAP theorem and its practical implications",
                        "Learn about consensus algorithms (Raft, Paxos)",
                        "Practice designing systems with eventual consistency",
                        "Build a small distributed key-value store"
                    ],
                    "resources": [
                        {
                            "type": "book",
                            "name": "Designing Data-Intensive Applications",
                            "url": "https://dataintensive.net",
                            "description": "The definitive guide to distributed systems design"
                        },
                        {
                            "type": "course",
                            "name": "MIT 6.824 Distributed Systems",
                            "url": "https://pdos.csail.mit.edu/6.824/",
                            "description": "World-class distributed systems course with hands-on labs"
                        }
                    ],
                    "estimated_time": "4-6 weeks"
                },
                {
                    "area": "Behavioral Interview Skills",
                    "current_level": "intermediate",
                    "target_level": "advanced",
                    "priority": "medium",
                    "action_items": [
                        "Prepare 8-10 STAR stories with specific metrics",
                        "Practice quantifying impact (percentages, user numbers)",
                        "Record yourself answering and review",
                        "Get feedback from peers on delivery"
                    ],
                    "resources": [
                        {
                            "type": "practice",
                            "name": "STAR Method Template",
                            "url": None,
                            "description": "Structure every behavioral answer as Situation-Task-Action-Result with metrics"
                        }
                    ],
                    "estimated_time": "1-2 weeks"
                },
                {
                    "area": "System Design depth",
                    "current_level": "intermediate",
                    "target_level": "advanced",
                    "priority": "high",
                    "action_items": [
                        "Practice 2-3 system design problems per week",
                        "Focus on cache invalidation strategies",
                        "Learn monitoring and observability patterns",
                        "Study real-world architectures (Netflix, Uber, Twitter)"
                    ],
                    "resources": [
                        {
                            "type": "book",
                            "name": "System Design Interview by Alex Xu",
                            "url": None,
                            "description": "Excellent practical guide to system design interviews"
                        },
                        {
                            "type": "practice",
                            "name": "System Design Primer (GitHub)",
                            "url": "https://github.com/donnemartin/system-design-primer",
                            "description": "Comprehensive open-source system design guide"
                        }
                    ],
                    "estimated_time": "3-4 weeks"
                }
            ],
            "strengths_to_leverage": [
                "Your full-stack experience is a strong differentiator — continue building end-to-end projects",
                "Your communication skills are above average — use this in system design rounds",
                "Your DSA fundamentals are solid — maintain practice to stay sharp"
            ],
            "30_day_plan": "Week 1-2: Focus on distributed systems fundamentals (read DDIA chapters 5-9, complete MIT 6.824 Lab 1). Prepare 5 STAR stories with metrics.\n\nWeek 2-3: Deep dive into system design (practice URL shortener, chat system, news feed designs). Study cache invalidation and eventual consistency patterns.\n\nWeek 3-4: Mock interviews focusing on weak areas. Record and review behavioral answers. Build a small distributed project for portfolio. Review and refine all preparation materials.",
            "next_interview_tips": [
                "Start system design answers with requirements clarification — show structured thinking",
                "Always quantify impact in behavioral answers (reduced latency by X%, served Y users)",
                "When discussing trade-offs, explicitly name what you're trading off and why",
                "Ask clarifying questions before diving into solutions — especially for DSA",
                "Practice thinking aloud — interviewers value your thought process as much as the answer"
            ],
            "overall_readiness": "almost_ready"
        })


async def generate_feedback(state: dict) -> dict:
    """Module-level convenience function for the orchestrator.

    Args:
        state: Pipeline state with ``scoring_result``.

    Returns:
        Updated state with ``feedback_result``.
    """
    agent = FeedbackAgent()
    return await agent.run(state)
