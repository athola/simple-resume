"""Tests for LLM config resolution."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from simple_resume.core.llm.protocol import LLMConfig
from simple_resume.shell.llm.config import resolve_api_key, resolve_llm_config


class TestResolveApiKey:
    def test_cli_arg_takes_priority(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}):
            key = resolve_api_key(cli_key="cli-key")
            assert key == "cli-key"

    def test_env_var_openai(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "openai-key"}, clear=False):
            key = resolve_api_key()
            assert key == "openai-key"

    def test_env_var_anthropic(self):
        env = {"ANTHROPIC_API_KEY": "anthropic-key"}
        with patch.dict("os.environ", env, clear=True):
            key = resolve_api_key()
            assert key == "anthropic-key"

    def test_returns_none_when_no_key_found(self):
        with patch.dict("os.environ", {}, clear=True):
            key = resolve_api_key()
            assert key is None

    def test_empty_cli_key_falls_through(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}):
            key = resolve_api_key(cli_key="")
            assert key == "env-key"


class TestResolveLLMConfig:
    def test_returns_config_with_resolved_key(self):
        config = resolve_llm_config(api_key="sk-test")
        assert isinstance(config, LLMConfig)
        assert config.api_key == "sk-test"

    def test_custom_model(self):
        config = resolve_llm_config(api_key="sk-test", model="gpt-4")
        assert config.model == "gpt-4"

    def test_default_model(self):
        config = resolve_llm_config(api_key="sk-test")
        assert config.model == "claude-sonnet-4-20250514"

    def test_raises_when_no_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key"):
                resolve_llm_config()

    def test_resolves_from_env_when_no_explicit_key(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}, clear=False):
            config = resolve_llm_config()
            assert config.api_key == "env-key"
