"""Tests for LLM exception types."""

from __future__ import annotations

from simple_resume.core.exceptions import (
    LLMError,
    LLMNotAvailableError,
    SimpleResumeError,
)


class TestLLMNotAvailableError:
    def test_inherits_from_simple_resume_error(self):
        err = LLMNotAvailableError("missing dep")
        assert isinstance(err, SimpleResumeError)

    def test_message(self):
        err = LLMNotAvailableError("Install with: pip install simple-resume[llm]")
        assert "Install with" in str(err)
        assert err.message == "Install with: pip install simple-resume[llm]"

    def test_install_hint_property(self):
        err = LLMNotAvailableError(
            "missing", install_hint="pip install simple-resume[llm]"
        )
        assert err.install_hint == "pip install simple-resume[llm]"

    def test_install_hint_default_none(self):
        err = LLMNotAvailableError("missing")
        assert err.install_hint is None

    def test_context_kwarg(self):
        err = LLMNotAvailableError("missing", context={"dep": "litellm"})
        assert err.context == {"dep": "litellm"}


class TestLLMError:
    def test_inherits_from_simple_resume_error(self):
        err = LLMError("API call failed")
        assert isinstance(err, SimpleResumeError)

    def test_message(self):
        err = LLMError("rate limited")
        assert str(err) == "rate limited"

    def test_provider_kwarg(self):
        err = LLMError("timeout", provider="openai")
        assert err.provider == "openai"

    def test_model_kwarg(self):
        err = LLMError("timeout", model="gpt-4")
        assert err.model == "gpt-4"

    def test_provider_default_none(self):
        err = LLMError("fail")
        assert err.provider is None
        assert err.model is None

    def test_context_kwarg(self):
        err = LLMError("fail", context={"status": 429})
        assert err.context == {"status": 429}
