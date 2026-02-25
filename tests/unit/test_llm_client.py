"""Tests for LLM client wrapper."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from simple_resume.core.exceptions import LLMError
from simple_resume.core.llm.protocol import LLMConfig, LLMProvider
from simple_resume.shell.llm.client import LiteLLMProvider


class TestLiteLLMProvider:
    def setup_method(self):
        self.config = LLMConfig(
            api_key="sk-test-key",
            model="gpt-4",
            temperature=0.3,
            max_tokens=4096,
        )

    def test_implements_llm_provider(self):
        assert issubclass(LiteLLMProvider, LLMProvider)

    def test_init_stores_config(self):
        provider = LiteLLMProvider(self.config)
        assert provider.config == self.config

    @patch("simple_resume.shell.llm.client.litellm")
    def test_complete_returns_text(self, mock_litellm):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello world"
        mock_litellm.completion.return_value = mock_response

        provider = LiteLLMProvider(self.config)
        result = provider.complete("Say hello")

        assert result == "Hello world"
        mock_litellm.completion.assert_called_once()

    @patch("simple_resume.shell.llm.client.litellm")
    def test_complete_with_system_prompt(self, mock_litellm):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "result"
        mock_litellm.completion.return_value = mock_response

        provider = LiteLLMProvider(self.config)
        provider.complete("user msg", system="system msg")

        call_kwargs = mock_litellm.completion.call_args
        messages = call_kwargs.kwargs["messages"]
        # Should have system and user messages
        assert any(m["role"] == "system" for m in messages)
        assert any(m["role"] == "user" for m in messages)

    @patch("simple_resume.shell.llm.client.litellm")
    def test_complete_wraps_exceptions(self, mock_litellm):
        mock_litellm.completion.side_effect = Exception("API timeout")

        provider = LiteLLMProvider(self.config)
        with pytest.raises(LLMError, match="API timeout"):
            provider.complete("test")

    @patch("simple_resume.shell.llm.client.litellm")
    def test_complete_structured_returns_dict(self, mock_litellm):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({"skills": ["python"]})
        mock_litellm.completion.return_value = mock_response

        provider = LiteLLMProvider(self.config)
        result = provider.complete_structured("extract skills", {"type": "object"})

        assert isinstance(result, dict)
        assert result["skills"] == ["python"]

    @patch("simple_resume.shell.llm.client.litellm")
    def test_complete_structured_invalid_json_raises(self, mock_litellm):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "not valid json"
        mock_litellm.completion.return_value = mock_response

        provider = LiteLLMProvider(self.config)
        with pytest.raises(LLMError, match="JSON"):
            provider.complete_structured("test", {"type": "object"})

    @patch("simple_resume.shell.llm.client.litellm")
    def test_complete_passes_config_to_litellm(self, mock_litellm):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ok"
        mock_litellm.completion.return_value = mock_response

        provider = LiteLLMProvider(self.config)
        provider.complete("test")

        call_kwargs = mock_litellm.completion.call_args[1]
        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["api_key"] == "sk-test-key"
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["max_tokens"] == 4096
