"""Base Agent class for all AI agents.

Provides shared LLM client initialisation, prompt template loading,
and structured JSON output parsing. All specialised agents inherit
from this class.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class BaseAgent:
    """Base class for all AI agents.

    Handles LLM client initialisation, prompt loading, and response parsing.
    Supports mock mode for development without API keys.

    Args:
        name: Human-readable agent name for logging.
        prompt_file: Filename of the prompt template (relative to ``prompts/``).
    """

    def __init__(self, name: str, prompt_file: str | None = None) -> None:
        self.name = name
        self.prompt_file = prompt_file
        self._prompt_template: str | None = None

    @property
    def prompt_template(self) -> str:
        """Lazy-load the prompt template from disk.

        Returns:
            The prompt template string.

        Raises:
            FileNotFoundError: If the prompt file does not exist.
        """
        if self._prompt_template is None and self.prompt_file:
            prompt_path = PROMPTS_DIR / self.prompt_file
            if prompt_path.exists():
                self._prompt_template = prompt_path.read_text(encoding="utf-8")
            else:
                raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return self._prompt_template or ""

    def format_prompt(self, **kwargs: Any) -> str:
        """Format the prompt template with the given variables.

        Args:
            **kwargs: Named template variables.

        Returns:
            The formatted prompt string.
        """
        return self.prompt_template.format(**kwargs)

    async def call_llm(self, prompt: str, system_message: str = "") -> str:
        """Call the OpenAI API and return the response text.

        Falls back to mock mode if no API key is configured or if the
        request fails.

        Args:
            prompt: The user message to send to the model.
            system_message: Optional system-level instruction.

        Returns:
            The raw text response from the model.
        """
        if not settings.has_openai_key:
            logger.info("[%s] No API key — using mock response", self.name)
            return await self._mock_response(prompt)

        try:
            from openai import AsyncOpenAI

            client_kwargs: dict = {"api_key": settings.openai_api_key}
            if settings.llm_base_url:
                client_kwargs["base_url"] = settings.llm_base_url

            client = AsyncOpenAI(**client_kwargs)

            messages: list[dict[str, str]] = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            return response.choices[0].message.content or ""

        except Exception as exc:
            logger.warning(
                "[%s] LLM call failed: %s — falling back to mock",
                self.name,
                exc,
            )
            return await self._mock_response(prompt)

    def parse_json_response(self, response: str) -> Any:
        """Parse JSON from an LLM response.

        Handles common formatting issues such as markdown code blocks
        and extraneous text surrounding the JSON payload.

        Args:
            response: Raw text response from the LLM.

        Returns:
            The parsed Python object (dict or list).
        """
        # Direct parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Extract from markdown code blocks
        json_match = re.search(
            r"```(?:json)?\s*\n(.*?)\n\s*```", response, re.DOTALL
        )
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Find bare JSON object or array
        for pattern in [r"\{.*?\}", r"\[.*?\]"]:
            # Find all possible matches and try parsing them
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

        return {"raw_response": response}

    async def _mock_response(self, prompt: str) -> str:
        """Return a mock response for development.

        Override in subclasses for agent-specific mock data.

        Args:
            prompt: The original prompt (unused in the default implementation).

        Returns:
            A JSON string containing mock data.
        """
        return json.dumps({
            "mock": True,
            "agent": self.name,
            "message": "Mock response — configure OPENAI_API_KEY for real results.",
        })

    async def run(self, state: dict) -> dict:
        """Execute the agent's primary task.

        Must be overridden by subclasses.

        Args:
            state: The shared pipeline state dictionary.

        Returns:
            The updated state dictionary.

        Raises:
            NotImplementedError: Always, unless overridden.
        """
        raise NotImplementedError(f"{self.name}.run() must be implemented")
