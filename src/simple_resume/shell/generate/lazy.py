"""Lazy-loaded generation functions for optimal import performance.

This module provides thin wrappers around the core generation functions
with lazy loading to reduce startup memory footprint.

.. versionadded:: 0.1.0
"""

from __future__ import annotations

import importlib
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, cast

from simple_resume.core.models import GenerationConfig

if TYPE_CHECKING:
    from simple_resume.core.result import BatchGenerationResult, GenerationResult
    from simple_resume.shell.generate.core import GenerateOptions


class _LazyCoreLoader:
    """Lazy loader for core generation functions."""

    def __init__(self) -> None:
        self._core: ModuleType | None = None
        self._loaded = False

    def _load_core(self) -> ModuleType:
        """Load core module if not already loaded."""
        if not self._loaded:
            self._core = importlib.import_module(".core", package=__package__)
            self._loaded = True
        if self._core is None:  # pragma: no cover
            raise RuntimeError("Failed to load core module")
        return self._core

    @property
    def generate_pdf(self) -> Any:
        """Get generate_pdf function from core module."""
        return self._load_core().generate_pdf

    @property
    def generate_html(self) -> Any:
        """Get generate_html function from core module."""
        return self._load_core().generate_html

    @property
    def generate_all(self) -> Any:
        """Get generate_all function from core module."""
        return self._load_core().generate_all

    @property
    def generate_resume(self) -> Any:
        """Get generate_resume function from core module."""
        return self._load_core().generate_resume

    @property
    def generate(self) -> Any:
        """Get generate function from core module."""
        return self._load_core().generate

    @property
    def preview(self) -> Any:
        """Get preview function from core module."""
        return self._load_core().preview


@lru_cache(maxsize=1)
def _get_lazy_core_loader() -> _LazyCoreLoader:
    """Provide a lazily created singleton loader without module globals."""
    return _LazyCoreLoader()


def generate_pdf(
    config: GenerationConfig,
    **config_overrides: Any,
) -> BatchGenerationResult:
    """Generate PDF resumes using a configuration object.

    Args:
        config: Generation configuration specifying sources, formats, and options.
        **config_overrides: Additional configuration overrides.

    Returns:
        BatchGenerationResult containing generated PDF files and metadata.

    Example:
        >>> from simple_resume import generate_pdf
        >>> from simple_resume.core.models import GenerationConfig
        >>> config = GenerationConfig(sources=["resume.yaml"], formats=["pdf"])
        >>> result = generate_pdf(config)
        >>> print(result.successful)

    .. versionadded:: 0.1.0

    """
    lazy_core = _get_lazy_core_loader()
    result: BatchGenerationResult = cast(
        "BatchGenerationResult", lazy_core.generate_pdf(config, **config_overrides)
    )
    return result


def generate_html(
    config: GenerationConfig,
    **config_overrides: Any,
) -> BatchGenerationResult:
    """Generate HTML resumes using a configuration object.

    Args:
        config: Generation configuration specifying sources, formats, and options.
        **config_overrides: Additional configuration overrides.

    Returns:
        BatchGenerationResult containing generated HTML files and metadata.

    Example:
        >>> from simple_resume import generate_html
        >>> from simple_resume.core.models import GenerationConfig
        >>> config = GenerationConfig(sources=["resume.yaml"], formats=["html"])
        >>> result = generate_html(config)

    .. versionadded:: 0.1.0

    """
    lazy_core = _get_lazy_core_loader()
    result: BatchGenerationResult = cast(
        "BatchGenerationResult", lazy_core.generate_html(config, **config_overrides)
    )
    return result


def generate_all(
    config: GenerationConfig,
    **config_overrides: Any,
) -> BatchGenerationResult:
    """Generate resumes in all specified formats.

    Args:
        config: Generation configuration specifying sources, formats, and options.
        **config_overrides: Additional configuration overrides.

    Returns:
        BatchGenerationResult containing all generated files and metadata.

    Example:
        >>> from simple_resume import generate_all
        >>> from simple_resume.core.models import GenerationConfig
        >>> config = GenerationConfig(sources=["resume.yaml"], formats=["pdf", "html"])
        >>> result = generate_all(config)

    .. versionadded:: 0.1.0

    """
    lazy_core = _get_lazy_core_loader()
    result: BatchGenerationResult = cast(
        "BatchGenerationResult", lazy_core.generate_all(config, **config_overrides)
    )
    return result


def generate_resume(
    config: GenerationConfig,
    **config_overrides: Any,
) -> GenerationResult:
    """Generate a single resume in a specific format.

    Args:
        config: Generation configuration specifying source and format.
        **config_overrides: Additional configuration overrides.

    Returns:
        GenerationResult for the generated resume.

    Example:
        >>> from simple_resume import generate_resume
        >>> from simple_resume.core.models import GenerationConfig
        >>> config = GenerationConfig(sources=["resume.yaml"], formats=["pdf"])
        >>> result = generate_resume(config)

    .. versionadded:: 0.1.0

    """
    lazy_core = _get_lazy_core_loader()
    result: GenerationResult = cast(
        "GenerationResult", lazy_core.generate_resume(config, **config_overrides)
    )
    return result


def generate(
    source: str | Path,
    options: GenerateOptions | None = None,
    **overrides: Any,
) -> dict[str, GenerationResult | BatchGenerationResult]:
    """Render one or more formats for the same source.

    This is the primary entry point for generating resumes. It accepts a
    source file path and optional configuration.

    Args:
        source: Path to the resume YAML file.
        options: Optional GenerateOptions with formats and settings.
        **overrides: Additional configuration overrides.

    Returns:
        Dictionary mapping format names to GenerationResult or BatchGenerationResult.

    Example:
        >>> from simple_resume import generate
        >>> result = generate("resume.yaml")
        >>> for fmt, r in result.items():
        ...     print(f"Generated {fmt}: {r}")

    .. versionadded:: 0.1.0

    """
    lazy_core = _get_lazy_core_loader()
    result: dict[str, GenerationResult | BatchGenerationResult] = cast(
        "dict[str, GenerationResult | BatchGenerationResult]",
        lazy_core.generate(source, options, **overrides),
    )
    return result


def preview(
    source: str | Path,
    *,
    data_dir: str | Path | None = None,
    template: str | None = None,
    browser: str | None = None,
    open_after: bool = True,
    **overrides: Any,
) -> GenerationResult | BatchGenerationResult:
    """Render a single resume to HTML and open in browser.

    This convenience function generates an HTML preview and optionally
    opens it in the default web browser.

    Args:
        source: Path to the resume YAML file.
        data_dir: Optional data directory override.
        template: Optional template name override.
        browser: Optional browser command (e.g., "firefox", "chrome").
        open_after: Whether to open the file after generation (default: True).
        **overrides: Additional configuration overrides.

    Returns:
        GenerationResult for the generated HTML preview.

    Example:
        >>> from simple_resume import preview
        >>> result = preview("resume.yaml")  # Opens in browser
        >>> result = preview("resume.yaml", open_after=False)  # Just generate

    .. versionadded:: 0.1.0

    """
    lazy_core = _get_lazy_core_loader()
    result: GenerationResult | BatchGenerationResult = cast(
        "GenerationResult | BatchGenerationResult",
        lazy_core.preview(
            source,
            data_dir=data_dir,
            template=template,
            browser=browser,
            open_after=open_after,
            **overrides,
        ),
    )
    return result


__all__ = [
    "generate_pdf",
    "generate_html",
    "generate_all",
    "generate_resume",
    "generate",
    "preview",
]
