"""Tests for shell/runtime/lazy_import.py module."""

from __future__ import annotations

from pathlib import Path

from simple_resume.shell.runtime.lazy_import import (
    LazyFunction,
    LazyModule,
    lazy_BatchGenerationResult,
    lazy_create_session,
    lazy_function,
    lazy_GenerationMetadata,
    lazy_GenerationResult,
    lazy_import,
    lazy_ResumeSession,
    lazy_SessionConfig,
    lazy_validate_directory_path,
    lazy_validate_format,
    lazy_validate_template_name,
)


class TestLazyModule:
    """Test LazyModule class."""

    def test_lazy_module_loads_on_attribute_access(self) -> None:
        """Test that module loads when attribute is accessed."""
        lazy_os = LazyModule("os")
        # Module should not be loaded yet
        assert lazy_os._loaded is False

        # Access an attribute to trigger load
        sep = lazy_os.sep
        assert lazy_os._loaded is True
        assert sep in {"/", "\\"}  # Unix or Windows

    def test_lazy_module_caches_after_load(self) -> None:
        """Test that module is cached after first load."""
        lazy_os = LazyModule("os")
        _ = lazy_os.sep  # First access
        module1 = lazy_os._module

        _ = lazy_os.path  # Second access
        module2 = lazy_os._module

        assert module1 is module2

    def test_lazy_module_dir(self) -> None:
        """Test __dir__ returns module directory."""
        lazy_os = LazyModule("os")
        dir_result = dir(lazy_os)
        assert "path" in dir_result
        assert "sep" in dir_result


class TestLazyFunction:
    """Test LazyFunction class."""

    def test_lazy_function_loads_on_call(self) -> None:
        """Test that function loads when called."""
        lazy_fn = LazyFunction("os.path", "exists")
        # Function should not be loaded yet
        assert lazy_fn._loaded is False

        # Call to trigger load
        result = lazy_fn("/")
        assert lazy_fn._loaded is True
        assert result is True

    def test_lazy_function_caches_after_load(self) -> None:
        """Test that function is cached after first load."""
        lazy_fn = LazyFunction("os.path", "join")
        _ = lazy_fn("a", "b")  # First call
        fn1 = lazy_fn._function

        _ = lazy_fn("c", "d")  # Second call
        fn2 = lazy_fn._function

        assert fn1 is fn2

    def test_lazy_function_passes_args_and_kwargs(self) -> None:
        """Test that args and kwargs are passed correctly."""
        lazy_fn = LazyFunction("os.path", "join")
        result = lazy_fn("a", "b", "c")
        assert result in {"a/b/c", "a\\b\\c"}


class TestLazyImportFunction:
    """Test lazy_import factory function."""

    def test_lazy_import_creates_lazy_module(self) -> None:
        """Test lazy_import creates LazyModule."""
        result = lazy_import("os")
        assert isinstance(result, LazyModule)

    def test_lazy_import_caches_results(self) -> None:
        """Test lazy_import returns same instance for same module."""
        result1 = lazy_import("os")
        result2 = lazy_import("os")
        assert result1 is result2


class TestLazyFunctionFactory:
    """Test lazy_function factory function."""

    def test_lazy_function_creates_lazy_function(self) -> None:
        """Test lazy_function creates LazyFunction."""
        result = lazy_function("os.path", "exists")
        assert isinstance(result, LazyFunction)

    def test_lazy_function_caches_results(self) -> None:
        """Test lazy_function returns same instance for same args."""
        result1 = lazy_function("os.path", "exists")
        result2 = lazy_function("os.path", "exists")
        assert result1 is result2


class TestLazyWrapperFunctions:
    """Test lazy wrapper functions for session and result modules."""

    def test_lazy_create_session(self) -> None:
        """Test lazy_create_session function works."""
        session = lazy_create_session()
        assert session is not None

    def test_lazy_ResumeSession(self) -> None:
        """Test lazy_ResumeSession function works."""
        session = lazy_ResumeSession()
        assert session is not None

    def test_lazy_SessionConfig(self) -> None:
        """Test lazy_SessionConfig function works."""
        config = lazy_SessionConfig()
        assert config is not None

    def test_lazy_GenerationResult(self, tmp_path: Path) -> None:
        """Test lazy_GenerationResult function works."""
        result = lazy_GenerationResult(
            output_path=tmp_path / "test.pdf",
            format_type="pdf",
        )
        assert result is not None
        assert result.format_type == "pdf"

    def test_lazy_BatchGenerationResult(self) -> None:
        """Test lazy_BatchGenerationResult function works."""
        result = lazy_BatchGenerationResult(results=[])
        assert result is not None
        assert len(result.results) == 0

    def test_lazy_GenerationMetadata(self) -> None:
        """Test lazy_GenerationMetadata function works."""
        metadata = lazy_GenerationMetadata(
            format_type="pdf",
            template_name="basic",
            generation_time=1.0,
            file_size=1000,
            resume_name="test",
        )
        assert metadata is not None
        assert metadata.format_type == "pdf"

    def test_lazy_validate_directory_path(self, tmp_path: Path) -> None:
        """Test lazy_validate_directory_path function works."""
        # Should return the path for valid directories
        result = lazy_validate_directory_path(tmp_path)
        assert result == tmp_path

    def test_lazy_validate_format(self) -> None:
        """Test lazy_validate_format function works."""
        result = lazy_validate_format("pdf")
        assert result == "pdf"

    def test_lazy_validate_template_name(self) -> None:
        """Test lazy_validate_template_name function works."""
        # Template names should not have extensions
        result = lazy_validate_template_name("resume_with_bars")
        assert result == "resume_with_bars"
