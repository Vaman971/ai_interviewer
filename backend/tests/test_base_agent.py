"""Tests for the BaseAgent class.

Covers prompt loading, JSON response parsing, LLM mock fallback,
and the abstract run method contract.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from agents.base_agent import BaseAgent


# ── Initialisation & Prompt Loading ──────────────────────────────


class TestBaseAgentInit:
    """Test agent construction and prompt template loading."""

    def test_init_stores_name(self) -> None:
        """Agent name is stored on the instance."""
        agent = BaseAgent(name="TestAgent")
        assert agent.name == "TestAgent"

    def test_init_without_prompt_file(self) -> None:
        """Agent can be created without a prompt file."""
        agent = BaseAgent(name="NoPrompt")
        assert agent.prompt_template == ""

    def test_prompt_template_loads_file(self, tmp_path: Path) -> None:
        """Prompt template is lazily loaded from disk."""
        prompt_file = tmp_path / "test_prompt.txt"
        prompt_file.write_text("Hello {name}", encoding="utf-8")

        agent = BaseAgent(name="Test", prompt_file="test_prompt.txt")
        with patch("agents.base_agent.PROMPTS_DIR", tmp_path):
            assert agent.prompt_template == "Hello {name}"

    def test_prompt_template_file_not_found(self, tmp_path: Path) -> None:
        """Missing prompt file raises FileNotFoundError."""
        agent = BaseAgent(name="Test", prompt_file="missing.txt")
        with patch("agents.base_agent.PROMPTS_DIR", tmp_path):
            with pytest.raises(FileNotFoundError):
                _ = agent.prompt_template

    def test_format_prompt(self, tmp_path: Path) -> None:
        """Format prompt substitutes template variables."""
        prompt_file = tmp_path / "greet.txt"
        prompt_file.write_text("Hi {user}, role: {role}", encoding="utf-8")

        agent = BaseAgent(name="Test", prompt_file="greet.txt")
        with patch("agents.base_agent.PROMPTS_DIR", tmp_path):
            result = agent.format_prompt(user="Alice", role="SDE")
        assert result == "Hi Alice, role: SDE"


# ── JSON Response Parsing ────────────────────────────────────────


class TestParseJsonResponse:
    """Test the parse_json_response method with various input formats."""

    def setup_method(self) -> None:
        """Create a shared BaseAgent instance for all tests."""
        self.agent = BaseAgent(name="ParserTest")

    def test_parse_valid_json_object(self) -> None:
        """Parse a standard JSON object."""
        raw = '{"key": "value", "number": 42}'
        result = self.agent.parse_json_response(raw)
        assert result == {"key": "value", "number": 42}

    def test_parse_valid_json_array(self) -> None:
        """Parse a JSON array."""
        raw = '[{"a": 1}, {"b": 2}]'
        result = self.agent.parse_json_response(raw)
        assert result == [{"a": 1}, {"b": 2}]

    def test_parse_json_in_markdown_code_block(self) -> None:
        """Extract JSON from a markdown code fence."""
        raw = 'Here is the analysis:\n```json\n{"skill": "Python"}\n```\nDone.'
        result = self.agent.parse_json_response(raw)
        assert result == {"skill": "Python"}

    def test_parse_json_in_plain_code_block(self) -> None:
        """Extract JSON from a code fence without language tag."""
        raw = '```\n{"score": 85}\n```'
        result = self.agent.parse_json_response(raw)
        assert result == {"score": 85}

    def test_parse_json_embedded_in_text(self) -> None:
        """Extract a JSON object embedded in surrounding text."""
        raw = 'The result is {"found": true} as expected.'
        result = self.agent.parse_json_response(raw)
        assert result == {"found": True}

    def test_parse_invalid_json_returns_raw(self) -> None:
        """Unparseable input is wrapped in a raw_response dict."""
        raw = "This is not JSON at all"
        result = self.agent.parse_json_response(raw)
        assert result == {"raw_response": raw}

    def test_parse_empty_string(self) -> None:
        """Empty string returns a raw_response dict."""
        result = self.agent.parse_json_response("")
        assert "raw_response" in result

    def test_parse_nested_json(self) -> None:
        """Parse deeply nested JSON structures."""
        nested = {"level1": {"level2": {"level3": [1, 2, 3]}}}
        raw = json.dumps(nested)
        result = self.agent.parse_json_response(raw)
        assert result == nested


# ── LLM Call & Mock Fallback ─────────────────────────────────────


class TestLLMCall:
    """Test call_llm behaviour and mock fallback."""

    @pytest.mark.asyncio
    async def test_mock_response_when_no_api_key(self) -> None:
        """Without an API key, call_llm returns mock response."""
        agent = BaseAgent(name="MockTest")
        with patch("agents.base_agent.settings") as mock_settings:
            mock_settings.has_openai_key = False
            response = await agent.call_llm("test prompt")

        parsed = json.loads(response)
        assert parsed["mock"] is True
        assert parsed["agent"] == "MockTest"

    @pytest.mark.asyncio
    async def test_default_mock_response_format(self) -> None:
        """Default _mock_response returns valid JSON with expected keys."""
        agent = BaseAgent(name="DefaultMock")
        response = await agent._mock_response("anything")
        parsed = json.loads(response)
        assert "mock" in parsed
        assert "agent" in parsed
        assert "message" in parsed

    @pytest.mark.asyncio
    async def test_run_raises_not_implemented(self) -> None:
        """Base run() raises NotImplementedError."""
        agent = BaseAgent(name="Abstract")
        with pytest.raises(NotImplementedError, match="Abstract.run"):
            await agent.run({})
