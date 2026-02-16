"""Lazy-loaded generation functions for optimal import performance.

This module provides thin wrappers around the core generation functions
with lazy loading to reduce startup memory footprint.

.. versionadded:: 0.1.0
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from simple_resume.core.models import GenerationConfig
from simple_resume.shell.runtime.lazy_import import lazy_import

if TYPE_CHECKING:
    from simple_resume.core.result import BatchGenerationResult, GenerationResult
    from simple_resume.shell.generate.core import GenerateOptions

# Single lazy module replaces the hand-rolled _LazyCoreLoader class
_lazy_core = lazy_import("simple_resume.shell.generate.core")


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
    lazy_core = _lazy_core
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
    lazy_core = _lazy_core
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
    lazy_core = _lazy_core
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
    lazy_core = _lazy_core
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
    lazy_core = _lazy_core
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
    lazy_core = _lazy_core
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
