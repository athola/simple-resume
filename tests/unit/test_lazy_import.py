"""Tests for lazy import utilities."""

from __future__ import annotations

import tempfile
from pathlib import Path

from simple_resume.constants import OutputFormat
from simple_resume.utils.lazy_import import (
    LazyFunction,
    LazyModule,
    lazy_create_session,
    lazy_function,
    lazy_import,
    lazy_ResumeSession,
    lazy_SessionConfig,
    lazy_validate_directory_path,
    lazy_validate_format,
    lazy_validate_template_name,
)


class TestLazyModule:
    """Test LazyModule class."""

    def test_lazy_module_delays_import(self) -> None:
        """Test that LazyModule doesn't import until accessed."""
        lazy_mod = LazyModule("simple_resume.constants")

        # Module should not be loaded yet
        assert lazy_mod._loaded is False
        assert lazy_mod._module is None

        # Access an attribute to trigger loading
        _ = lazy_mod.OutputFormat

        # Now it should be loaded
        assert lazy_mod._loaded is True
        assert lazy_mod._module is not None

    def test_lazy_module_getattr(self) -> None:
        """Test __getattr__ on LazyModule."""
        lazy_mod = LazyModule("simple_resume.constants")

        # Access an attribute
        output_format = lazy_mod.OutputFormat

        # Should have loaded the real module
        assert output_format is not None
        assert hasattr(output_format, "PDF")

    def test_lazy_module_dir(self) -> None:
        """Test __dir__ on LazyModule."""
        lazy_mod = LazyModule("simple_resume.constants")

        # Get directory listing
        attrs = dir(lazy_mod)

        # Should contain expected constants
        assert "OutputFormat" in attrs
        assert "RenderMode" in attrs

    def test_lazy_module_caches_import(self) -> None:
        """Test that LazyModule caches the imported module."""
        lazy_mod = LazyModule("simple_resume.constants")

        # Access twice
        _ = lazy_mod.OutputFormat
        first_module = lazy_mod._module

        _ = lazy_mod.RenderMode
        second_module = lazy_mod._module

        # Should be the same module object
        assert first_module is second_module


class TestLazyFunction:
    """Test LazyFunction class."""

    def test_lazy_function_delays_import(self) -> None:
        """Test that LazyFunction doesn't import until called."""
        lazy_func = LazyFunction("simple_resume.validation", "validate_format")

        # Function should not be loaded yet
        assert lazy_func._loaded is False
        assert lazy_func._function is None

        # Call the function to trigger loading

        result = lazy_func("pdf")

        # Now it should be loaded
        assert lazy_func._loaded is True
        assert lazy_func._function is not None
        assert result == OutputFormat.PDF

    def test_lazy_function_call(self) -> None:
        """Test calling a LazyFunction."""
        lazy_func = LazyFunction("simple_resume.validation", "validate_format")

        # Call the function

        result = lazy_func("html")

        # Should return expected result
        assert result == OutputFormat.HTML

    def test_lazy_function_with_args_and_kwargs(self) -> None:
        """Test LazyFunction with positional and keyword arguments."""
        lazy_func = LazyFunction("simple_resume.validation", "validate_format")

        # Call with positional argument and keyword argument

        result = lazy_func("pdf", param_name="test_param")

        assert result == OutputFormat.PDF

    def test_lazy_function_caches_import(self) -> None:
        """Test that LazyFunction caches the imported function."""
        lazy_func = LazyFunction("simple_resume.validation", "validate_format")

        # Call twice

        _ = lazy_func("pdf")
        first_func = lazy_func._function

        _ = lazy_func("html")
        second_func = lazy_func._function

        # Should be the same function object
        assert first_func is second_func


class TestLazyImportFunctions:
    """Test the lazy import helper functions."""

    def test_lazy_import_creates_lazy_module(self) -> None:
        """Test lazy_import creates a LazyModule."""
        lazy_mod = lazy_import("simple_resume.constants")

        assert isinstance(lazy_mod, LazyModule)
        assert lazy_mod._module_name == "simple_resume.constants"

    def test_lazy_import_caches_instances(self) -> None:
        """Test lazy_import caches module instances."""
        lazy_mod1 = lazy_import("simple_resume.constants")
        lazy_mod2 = lazy_import("simple_resume.constants")

        # Should be the same instance due to lru_cache
        assert lazy_mod1 is lazy_mod2

    def test_lazy_function_creates_lazy_function(self) -> None:
        """Test lazy_function creates a LazyFunction."""
        lazy_func = lazy_function("simple_resume.validation", "validate_format")

        assert isinstance(lazy_func, LazyFunction)
        assert lazy_func._module_path == "simple_resume.validation"
        assert lazy_func._function_name == "validate_format"

    def test_lazy_function_caches_instances(self) -> None:
        """Test lazy_function caches function instances."""
        lazy_func1 = lazy_function("simple_resume.validation", "validate_format")
        lazy_func2 = lazy_function("simple_resume.validation", "validate_format")

        # Should be the same instance due to lru_cache
        assert lazy_func1 is lazy_func2


class TestLazyWrappers:
    """Test the lazy wrapper functions exposed in the module."""

    def test_lazy_validate_format(self) -> None:
        """Test lazy_validate_format wrapper."""

        result = lazy_validate_format("pdf")
        assert result == OutputFormat.PDF

    def test_lazy_validate_template_name(self) -> None:
        """Test lazy_validate_template_name wrapper."""

        # Should not raise for valid template
        result = lazy_validate_template_name("professional")
        assert result == "professional"

    def test_lazy_validate_directory_path(self) -> None:
        """Test lazy_validate_directory_path wrapper."""

        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            result = lazy_validate_directory_path(tmpdir)
            assert result == Path(tmpdir)

    def test_lazy_create_session(self) -> None:
        """Test lazy_create_session wrapper."""

        # Create a session with a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            session = lazy_create_session(data_dir=tmpdir)
            assert session is not None

    def test_lazy_resume_session(self) -> None:
        """Test lazy_ResumeSession wrapper."""

        # Create a ResumeSession with a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            session = lazy_ResumeSession(data_dir=tmpdir)
            assert session is not None

    def test_lazy_session_config(self) -> None:
        """Test lazy_SessionConfig wrapper."""

        # Create a SessionConfig with default settings
        config = lazy_SessionConfig()
        assert config is not None
