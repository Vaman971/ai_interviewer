"""DSA Agent.

Generates coding problems (data structures and algorithms) and
evaluates submitted code solutions.
"""

import json
from agents.base_agent import BaseAgent


class DSAAgent(BaseAgent):
    """Agent that generates coding problems and evaluates solutions.

    Produces problems with descriptions, examples, constraints,
    hints, test cases, and solution templates.
    """

    def __init__(self) -> None:
        super().__init__(name="DSAAgent", prompt_file="dsa.txt")

    async def run(self, state: dict) -> dict:
        """Generate DSA problems based on the candidate profile.

        Args:
            state: Should contain ``jd_analysis`` and ``difficulty_level``.

        Returns:
            The state updated with ``dsa_problems`` (list[dict]).
        """
        jd_analysis = state.get("jd_analysis", {})
        experience_level = "mid"
        role_type = "fullstack"
        if isinstance(jd_analysis, dict):
            experience_level = jd_analysis.get("experience_level", "mid")
            role_type = jd_analysis.get("role_type", "fullstack")

        difficulty = state.get("difficulty_level", "medium")

        prompt = self.format_prompt(
            experience_level=experience_level,
            difficulty=difficulty,
            focus_area="data structures and algorithms",
            role_type=role_type,
        )

        response = await self.call_llm(
            prompt,
            system_message="You are a DSA interviewer. Generate a coding problem. Always respond with valid JSON."
        )
        parsed = self.parse_json_response(response)

        if isinstance(parsed, list):
            state["dsa_problems"] = parsed
        else:
            state["dsa_problems"] = [parsed]

        return state

    async def evaluate_code(
        self,
        problem: dict,
        code: str,
        language: str = "python",
    ) -> dict:
        """Evaluate submitted code against the problem's test cases.

        Args:
            problem: The DSA problem definition.
            code: The candidate's submitted source code.
            language: Programming language of the submission.

        Returns:
            Dictionary with correctness, complexity analysis, and feedback.
        """
        eval_prompt = f"""
Evaluate the following code solution for the problem: {problem.get('title', 'Unknown')}

Problem: {problem.get('description', '')}

Submitted Code ({language}):
```{language}
{code}
```

Test Cases: {json.dumps(problem.get('test_cases', []))}

Evaluate and return JSON:
{{
    "is_correct": true/false,
    "test_results": [{{"input": "...", "expected": "...", "actual": "...", "passed": true/false}}],
    "time_complexity": "estimated time complexity",
    "space_complexity": "estimated space complexity",
    "code_quality": "assessment of code quality, style, and readability",
    "score": <0-10>,
    "feedback": "detailed feedback",
    "suggestions": ["improvement suggestions"]
}}
"""
        response = await self.call_llm(
            eval_prompt,
            system_message="You are a code evaluator. Analyze code correctness and quality. Always respond with valid JSON."
        )
        return self.parse_json_response(response)

    async def _mock_response(self, prompt: str) -> str:
        """Return mock DSA problem data.

        Args:
            prompt: The original prompt (unused).

        Returns:
            JSON string with a sample coding problem.
        """
        return json.dumps({
            "title": "Two Sum",
            "difficulty": "easy",
            "category": "hash_maps",
            "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\n\nYou may assume that each input would have exactly one solution, and you may not use the same element twice.\n\nYou can return the answer in any order.",
            "examples": [
                {
                    "input": "nums = [2,7,11,15], target = 9",
                    "output": "[0, 1]",
                    "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1]."
                },
                {
                    "input": "nums = [3,2,4], target = 6",
                    "output": "[1, 2]",
                    "explanation": "Because nums[1] + nums[2] == 6, we return [1, 2]."
                }
            ],
            "constraints": [
                "2 <= nums.length <= 10^4",
                "-10^9 <= nums[i] <= 10^9",
                "-10^9 <= target <= 10^9",
                "Only one valid answer exists."
            ],
            "hints": [
                "Think about how you can use a data structure to speed up the lookup.",
                "A hash map can help you find the complement in O(1) time.",
                "For each element, check if target - element exists in the hash map."
            ],
            "expected_approach": "Use a hash map to store values and their indices. For each element, check if the complement exists.",
            "time_complexity": "O(n)",
            "space_complexity": "O(n)",
            "test_cases": [
                {"input": "[2,7,11,15], 9", "expected_output": "[0, 1]"},
                {"input": "[3,2,4], 6", "expected_output": "[1, 2]"},
                {"input": "[3,3], 6", "expected_output": "[0, 1]"}
            ],
            "solution_template": "def two_sum(nums: list[int], target: int) -> list[int]:\n    # Your code here\n    pass"
        })


async def generate_dsa_problems(state: dict) -> dict:
    """Module-level convenience function for the orchestrator.

    Args:
        state: Pipeline state with JD analysis and difficulty.

    Returns:
        Updated state with ``dsa_problems``.
    """
    agent = DSAAgent()
    return await agent.run(state)
