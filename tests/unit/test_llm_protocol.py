"""Tests for LLM protocol and config types."""

from __future__ import annotations

from abc import ABC
from dataclasses import FrozenInstanceError

import pytest

from simple_resume.core.llm.protocol import LLMConfig, LLMProvider


class TestLLMConfig:
    def test_create_with_required_fields(self):
        config = LLMConfig(api_key="sk-test123")
        assert config.api_key == "sk-test123"

    def test_default_model(self):
        config = LLMConfig(api_key="sk-test")
        assert config.model == "claude-sonnet-4-20250514"

    def test_default_temperature(self):
        config = LLMConfig(api_key="sk-test")
        assert config.temperature == 0.3

    def test_default_max_tokens(self):
        config = LLMConfig(api_key="sk-test")
        assert config.max_tokens == 4096

    def test_custom_values(self):
        config = LLMConfig(
            api_key="sk-test",
            model="gpt-4",
            temperature=0.7,
            max_tokens=2048,
        )
        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 2048

    def test_frozen(self):
        config = LLMConfig(api_key="sk-test")
        with pytest.raises(FrozenInstanceError):
            config.api_key = "changed"  # type: ignore[misc]

    def test_equality(self):
        c1 = LLMConfig(api_key="sk-test", model="gpt-4")
        c2 = LLMConfig(api_key="sk-test", model="gpt-4")
        assert c1 == c2

    def test_inequality(self):
        c1 = LLMConfig(api_key="sk-test", model="gpt-4")
        c2 = LLMConfig(api_key="sk-test", model="gpt-3.5-turbo")
        assert c1 != c2


class TestLLMProvider:
    def test_is_abstract(self):
        assert issubclass(LLMProvider, ABC)

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            LLMProvider()  # type: ignore[abstract]

    def test_subclass_must_implement_complete(self):
        class IncompleteProvider(LLMProvider):
            def complete_structured(self, prompt, schema, **kwargs):
                return {}

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore[abstract]

    def test_subclass_must_implement_complete_structured(self):
        class IncompleteProvider(LLMProvider):
            def complete(self, prompt, system="", **kwargs):
                return ""

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore[abstract]

    def test_valid_subclass(self):
        class MockProvider(LLMProvider):
            def complete(self, prompt, system="", **kwargs):
                return "response"

            def complete_structured(self, prompt, schema, **kwargs):
                return {"key": "value"}

        provider = MockProvider()
        assert provider.complete("test") == "response"
        assert provider.complete_structured("test", {}) == {"key": "value"}
