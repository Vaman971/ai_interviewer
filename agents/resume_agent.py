"""Resume Analyzer Agent.

Extracts a structured candidate profile from resume text using the LLM.
"""

import json

from agents.base_agent import BaseAgent


class ResumeAgent(BaseAgent):
    """Agent that analyses resume text and extracts a structured profile.

    Produces a dictionary containing skills, experience, projects,
    education, and professional strengths.
    """

    def __init__(self) -> None:
        super().__init__(name="ResumeAgent", prompt_file="resume_analysis.txt")

    async def run(self, state: dict) -> dict:
        """Analyse resume text and enrich the pipeline state.

        Args:
            state: Must contain ``resume_text`` (str).

        Returns:
            The state updated with ``resume_analysis`` (dict).
        """
        resume_text = state.get("resume_text", "")
        if not resume_text:
            state["resume_analysis"] = {"error": "No resume text provided"}
            return state

        prompt = self.format_prompt(resume_text=resume_text)
        response = await self.call_llm(
            prompt,
            system_message=(
                "You are an expert resume analyzer. "
                "Always respond with valid JSON."
            ),
        )
        state["resume_analysis"] = self.parse_json_response(response)
        return state

    async def _mock_response(self, prompt: str) -> str:
        """Return mock resume analysis data.

        Args:
            prompt: The original prompt (unused).

        Returns:
            JSON string with sample candidate profile.
        """
        return json.dumps({
            "skills": [
                "Python", "JavaScript", "TypeScript", "React", "Node.js",
                "FastAPI", "PostgreSQL", "Docker", "AWS", "Git",
                "REST APIs", "GraphQL", "CI/CD", "Agile", "Problem Solving",
            ],
            "experience_years": 3.5,
            "experience_summary": (
                "Full-stack developer with 3.5 years experience "
                "building scalable web applications."
            ),
            "projects": [
                {
                    "name": "E-Commerce Platform",
                    "description": (
                        "Built a full-stack e-commerce platform "
                        "with real-time inventory management"
                    ),
                    "technologies": ["React", "Node.js", "PostgreSQL", "Redis"],
                    "impact": "Served 10K+ daily users with 99.9% uptime",
                },
                {
                    "name": "Task Management API",
                    "description": (
                        "RESTful API for task management with "
                        "authentication and real-time updates"
                    ),
                    "technologies": ["FastAPI", "PostgreSQL", "WebSocket"],
                    "impact": "Reduced team task tracking overhead by 40%",
                },
            ],
            "education": [
                {
                    "degree": "B.Tech Computer Science",
                    "institution": "Indian Institute of Technology",
                    "year": "2021",
                    "gpa": "8.5/10",
                },
            ],
            "strengths": [
                "Strong full-stack development skills",
                "Experience with cloud infrastructure",
                "Good understanding of system design",
            ],
            "certifications": ["AWS Solutions Architect Associate"],
            "summary": (
                "Experienced full-stack developer with strong Python "
                "and JavaScript skills, focused on building scalable "
                "web applications with modern frameworks."
            ),
        })


async def analyze_resume(state: dict) -> dict:
    """Module-level convenience function for the orchestrator.

    Args:
        state: Pipeline state with ``resume_text``.

    Returns:
        Updated state with ``resume_analysis``.
    """
    agent = ResumeAgent()
    return await agent.run(state)
