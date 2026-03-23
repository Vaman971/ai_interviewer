"""Question Generator Agent.

Generates personalised interview questions based on skill gap analysis,
candidate profile, and interview settings.
"""

import json
from agents.base_agent import BaseAgent


class QuestionAgent(BaseAgent):
    """Agent that generates a tailored set of interview questions.

    Uses resume analysis, JD analysis, and skill gap data to create
    questions across behavioral, technical, DSA, and system design.
    """

    def __init__(self) -> None:
        super().__init__(name="QuestionAgent", prompt_file="question_generation.txt")

    async def run(self, state: dict) -> dict:
        """Generate interview questions and enrich the pipeline state.

        Args:
            state: Must contain ``resume_analysis``, ``jd_analysis``,
                ``skill_gap_report``, and interview settings.

        Returns:
            The state updated with ``questions`` (list[dict]).
        """
        resume_analysis = state.get("resume_analysis", {})
        jd_analysis = state.get("jd_analysis", {})
        skill_gap_report = state.get("skill_gap_report", {})
        interview_type = state.get("interview_type", "full")
        personality_mode = state.get("personality_mode", "professional")
        difficulty_level = state.get("difficulty_level", "medium")

        # Determine role info from JD analysis
        role_type = jd_analysis.get("role_type", "fullstack") if isinstance(jd_analysis, dict) else "fullstack"
        experience_level = jd_analysis.get("experience_level", "mid") if isinstance(jd_analysis, dict) else "mid"

        prompt = self.format_prompt(
            resume_analysis=json.dumps(resume_analysis, indent=2),
            jd_analysis=json.dumps(jd_analysis, indent=2),
            skill_gap_report=json.dumps(skill_gap_report, indent=2),
            interview_type=interview_type,
            role_type=role_type,
            experience_level=experience_level,
            personality_mode=personality_mode,
            difficulty_level=difficulty_level,
        )

        response = await self.call_llm(
            prompt,
            system_message="You are a senior technical interviewer preparing personalized questions. Always respond with a valid JSON array."
        )

        parsed = self.parse_json_response(response)

        # Handle both array and object with questions key
        if isinstance(parsed, list):
            state["questions"] = parsed
        elif isinstance(parsed, dict) and "questions" in parsed:
            state["questions"] = parsed["questions"]
        else:
            state["questions"] = [parsed]

        return state

    async def _mock_response(self, prompt: str) -> str:
        """Return mock interview questions.

        Args:
            prompt: The original prompt (unused).

        Returns:
            JSON string with sample interview questions array.
        """
        return json.dumps([
            {
                "text": "Tell me about a time you had to make a critical technical decision under pressure. What was the context, your approach, and the outcome?",
                "type": "behavioral",
                "difficulty": "medium",
                "category": "Decision Making",
                "expected_answer_points": [
                    "Clear problem description",
                    "Structured decision-making process",
                    "Considered trade-offs",
                    "Measurable outcome"
                ],
                "follow_up": "How would you approach it differently with what you know now?",
                "time_limit_minutes": 5
            },
            {
                "text": "Can you walk me through the architecture of your E-Commerce Platform project? What were the key design decisions and why?",
                "type": "resume_deep_dive",
                "difficulty": "medium",
                "category": "System Architecture",
                "expected_answer_points": [
                    "Clear architecture diagram explanation",
                    "Justification for technology choices",
                    "Scalability considerations",
                    "Trade-offs acknowledged"
                ],
                "follow_up": "How would you scale it to handle 100x the current traffic?",
                "time_limit_minutes": 8
            },
            {
                "text": "Design a REST API for a task management system. Include endpoints, request/response formats, authentication, and error handling.",
                "type": "technical",
                "difficulty": "medium",
                "category": "API Design",
                "expected_answer_points": [
                    "RESTful endpoint naming",
                    "Proper HTTP methods and status codes",
                    "Authentication strategy (JWT)",
                    "Pagination and filtering",
                    "Error response format"
                ],
                "follow_up": "How would you add real-time notifications for task updates?",
                "time_limit_minutes": 10
            },
            {
                "text": "Explain the difference between SQL and NoSQL databases. When would you choose one over the other? Give specific examples from your experience.",
                "type": "technical",
                "difficulty": "medium",
                "category": "Database Design",
                "expected_answer_points": [
                    "ACID vs BASE properties",
                    "Schema flexibility",
                    "Scalability patterns",
                    "Real-world use cases",
                    "Personal experience examples"
                ],
                "follow_up": "How would you handle a scenario where you need both relational and document storage?",
                "time_limit_minutes": 7
            },
            {
                "text": "Given an array of integers, find two numbers that add up to a specific target. Return their indices. What is the optimal time complexity?",
                "type": "dsa",
                "difficulty": "easy",
                "category": "Hash Maps / Arrays",
                "expected_answer_points": [
                    "Brute force O(n²) approach",
                    "Optimized O(n) hash map approach",
                    "Handle edge cases (duplicates, no solution)",
                    "Clean code implementation"
                ],
                "follow_up": "What if the array is sorted? Can you do better than O(n) space?",
                "time_limit_minutes": 10
            },
            {
                "text": "Design a URL shortening service like bit.ly. Walk me through the high-level architecture, data storage, and handling of high traffic.",
                "type": "system_design",
                "difficulty": "medium",
                "category": "System Design",
                "expected_answer_points": [
                    "URL encoding strategy (base62)",
                    "Database schema design",
                    "Caching layer (Redis)",
                    "Load balancing",
                    "Analytics tracking",
                    "Scalability plan"
                ],
                "follow_up": "How would you handle custom short URLs and analytics?",
                "time_limit_minutes": 15
            },
            {
                "text": "You notice your application's API response times have increased from 100ms to 2 seconds. Walk me through your debugging process.",
                "type": "technical",
                "difficulty": "hard",
                "category": "Performance & Debugging",
                "expected_answer_points": [
                    "Systematic debugging approach",
                    "Monitoring and logging tools",
                    "Common bottlenecks (DB queries, N+1, network)",
                    "Profiling techniques",
                    "Resolution and prevention"
                ],
                "follow_up": "How would you set up monitoring to catch this proactively?",
                "time_limit_minutes": 8
            },
            {
                "text": "Tell me about a conflict you had with a teammate about a technical approach. How did you resolve it?",
                "type": "behavioral",
                "difficulty": "medium",
                "category": "Collaboration",
                "expected_answer_points": [
                    "Specific situation",
                    "Active listening",
                    "Data-driven resolution",
                    "Positive outcome",
                    "Lesson learned"
                ],
                "follow_up": "What would you do if the disagreement was with a more senior engineer?",
                "time_limit_minutes": 5
            }
        ])


async def generate_questions(state: dict) -> dict:
    """Module-level convenience function for the orchestrator.

    Args:
        state: Pipeline state with analysis data.

    Returns:
        Updated state with ``questions``.
    """
    agent = QuestionAgent()
    return await agent.run(state)
