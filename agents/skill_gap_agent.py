"""Skill Gap Agent.

Compares the candidate's resume profile against JD requirements
to identify matching, missing, and additional skills.
"""

import json
from agents.base_agent import BaseAgent


class SkillGapAgent(BaseAgent):
    """Agent that identifies skill gaps between candidate and role.

    Compares resume analysis with JD analysis and produces a
    structured gap report with recommendations.
    """

    def __init__(self) -> None:
        super().__init__(name="SkillGapAgent", prompt_file="skill_gap.txt")

    async def run(self, state: dict) -> dict:
        """Compare resume and JD analyses to identify gaps.

        Args:
            state: Must contain ``resume_analysis`` and ``jd_analysis``.

        Returns:
            The state updated with ``skill_gap_report`` (dict).
        """
        resume_analysis = state.get("resume_analysis", {})
        jd_analysis = state.get("jd_analysis", {})

        if not resume_analysis or not jd_analysis:
            state["skill_gap_report"] = {"error": "Missing resume or JD analysis"}
            return state

        prompt = self.format_prompt(
            resume_analysis=json.dumps(resume_analysis, indent=2),
            jd_analysis=json.dumps(jd_analysis, indent=2),
        )
        response = await self.call_llm(
            prompt,
            system_message="You are an expert career advisor analyzing skill gaps. Always respond with valid JSON."
        )
        state["skill_gap_report"] = self.parse_json_response(response)
        return state

    async def _mock_response(self, prompt: str) -> str:
        """Return mock skill gap analysis data.

        Args:
            prompt: The original prompt (unused).

        Returns:
            JSON string with sample skill gap report.
        """
        return json.dumps({
            "matching_skills": [
                "Python", "JavaScript", "React", "Node.js",
                "PostgreSQL", "Docker", "REST APIs", "Git"
            ],
            "missing_skills": [
                "Kubernetes", "System Design at scale"
            ],
            "partial_skills": [
                "AWS (has basic experience, needs deeper knowledge)",
                "CI/CD (familiar but not lead-level)"
            ],
            "additional_skills": [
                "FastAPI", "GraphQL"
            ],
            "gap_severity": "medium",
            "experience_gap": {
                "required_years": 4,
                "candidate_years": 3.5,
                "assessment": "slightly-under"
            },
            "recommendations": [
                "Strengthen system design knowledge — practice designing large-scale systems",
                "Get hands-on with Kubernetes — deploy a multi-service application",
                "Deepen AWS knowledge — focus on ECS, RDS, and CloudFormation",
                "Prepare behavioral examples of technical leadership"
            ],
            "focus_areas": [
                "System design", "Kubernetes/container orchestration",
                "Leadership & mentoring examples", "Advanced database optimization"
            ],
            "overall_fit_score": 72
        })


async def analyze_skill_gap(state: dict) -> dict:
    """Module-level convenience function for the orchestrator.

    Args:
        state: Pipeline state with ``resume_analysis`` and ``jd_analysis``.

    Returns:
        Updated state with ``skill_gap_report``.
    """
    agent = SkillGapAgent()
    return await agent.run(state)
