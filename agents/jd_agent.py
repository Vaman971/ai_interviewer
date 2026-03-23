"""JD Analyzer Agent.

Extracts structured role requirements from job description text
using the LLM.
"""

import json
from agents.base_agent import BaseAgent


class JDAgent(BaseAgent):
    """Agent that analyses job description text.

    Produces a dictionary containing role title, required/preferred
    skills, experience level, and responsibilities.
    """

    def __init__(self) -> None:
        super().__init__(name="JDAgent", prompt_file="jd_analysis.txt")

    async def run(self, state: dict) -> dict:
        """Analyse JD text and enrich the pipeline state.

        Args:
            state: Must contain ``jd_text`` (str).

        Returns:
            The state updated with ``jd_analysis`` (dict).
        """
        jd_text = state.get("jd_text", "")
        if not jd_text:
            state["jd_analysis"] = {"error": "No JD text provided"}
            return state

        prompt = self.format_prompt(jd_text=jd_text)
        response = await self.call_llm(
            prompt,
            system_message="You are an expert job description analyzer. Always respond with valid JSON."
        )
        state["jd_analysis"] = self.parse_json_response(response)
        return state

    async def _mock_response(self, prompt: str) -> str:
        """Return mock JD analysis data.

        Args:
            prompt: The original prompt (unused).

        Returns:
            JSON string with sample JD analysis.
        """
        return json.dumps({
            "role_title": "Senior Full Stack Developer",
            "company": "TechCorp Inc.",
            "required_skills": [
                "Python", "JavaScript/TypeScript", "React", "Node.js",
                "PostgreSQL", "Docker", "REST APIs", "Git"
            ],
            "preferred_skills": [
                "Kubernetes", "AWS/GCP", "GraphQL", "Redis",
                "CI/CD", "Microservices", "System Design"
            ],
            "experience_level": "senior",
            "experience_years_min": 4,
            "experience_years_max": 8,
            "responsibilities": [
                "Design and develop scalable web applications",
                "Lead technical architecture decisions",
                "Mentor junior developers",
                "Implement CI/CD pipelines",
                "Conduct code reviews"
            ],
            "qualifications": [
                "B.Tech/B.E. in Computer Science or equivalent",
                "4+ years of professional development experience",
                "Strong understanding of software design patterns"
            ],
            "role_type": "fullstack",
            "domain": "SaaS / Enterprise Software",
            "interview_focus_areas": [
                "System design", "Data structures & algorithms",
                "API design", "Database optimization", "Cloud architecture"
            ],
            "salary_range": None
        })


async def analyze_jd(state: dict) -> dict:
    """Module-level convenience function for the orchestrator.

    Args:
        state: Pipeline state with ``jd_text``.

    Returns:
        Updated state with ``jd_analysis``.
    """
    agent = JDAgent()
    return await agent.run(state)
