"""Tests for LLM feature gating."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from simple_resume.core.exceptions import LLMNotAvailableError
from simple_resume.shell.llm.gate import is_llm_available, requires_llm


class TestIsLLMAvailable:
    def test_returns_true_when_litellm_importable(self):
        with patch.dict("sys.modules", {"litellm": object()}):
            assert is_llm_available() is True

    def test_returns_false_when_litellm_not_importable(self):
        with patch.dict("sys.modules", {"litellm": None}):
            # When module is set to None in sys.modules, import raises ImportError
            assert is_llm_available() is False


class TestRequiresLLM:
    def test_decorated_function_runs_when_available(self):
        @requires_llm
        def my_func(x: int) -> int:
            return x * 2

        with patch("simple_resume.shell.llm.gate.is_llm_available", return_value=True):
            assert my_func(5) == 10

    def test_decorated_function_raises_when_unavailable(self):
        @requires_llm
        def my_func() -> str:
            return "should not reach"

        with patch("simple_resume.shell.llm.gate.is_llm_available", return_value=False):
            with pytest.raises(LLMNotAvailableError, match="simple-resume\\[llm\\]"):
                my_func()

    def test_preserves_function_name(self):
        @requires_llm
        def my_special_func() -> None:
            pass

        assert my_special_func.__name__ == "my_special_func"

    def test_preserves_docstring(self):
        @requires_llm
        def documented_func() -> None:
            """Return my docstring."""

        assert documented_func.__doc__ == "Return my docstring."

    def test_passes_args_and_kwargs(self):
        @requires_llm
        def func_with_args(a: int, b: str, c: bool = False) -> tuple:
            return (a, b, c)

        with patch("simple_resume.shell.llm.gate.is_llm_available", return_value=True):
            assert func_with_args(1, "hello", c=True) == (1, "hello", True)
