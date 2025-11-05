"""Unified generation functions with standardized parameter patterns.

This module provides pandas-style unified generation functions with consistent
parameter patterns across all operations.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Paths
from .constants import DEFAULT_FORMAT
from .exceptions import (
    ConfigurationError,
    FileSystemError,
    GenerationError,
    ValidationError,
)
from .result import BatchGenerationResult, GenerationResult
from .session import ResumeSession, SessionConfig
from .validation import validate_directory_path, validate_format, validate_template_name


@dataclass(frozen=True)
class GenerationConfig:
    """Complete configuration for generation operations."""

    # Path configuration
    data_dir: str | Path | None = None
    output_dir: str | Path | None = None
    output_path: str | Path | None = None  # For specific output path
    paths: Paths | None = None

    # Generation options
    template: str | None = None
    format: str = "pdf"
    open_after: bool = False
    preview: bool = False
    name: str | None = None
    pattern: str = "*"
    browser: str | None = None  # For HTML generation
    formats: list[str] | None = None  # For generate_all


def _generate_pdf_impl(
    config: GenerationConfig,
    **config_overrides: Any,
) -> GenerationResult | BatchGenerationResult:
    """Generate PDFs using the provided configuration helper."""
    time.time()

    try:
        # Validate inputs using configuration object
        template = config.template
        if template:
            template = validate_template_name(template)

        if config.data_dir:
            validate_directory_path(config.data_dir, must_exist=True)

        if config.output_dir:
            validate_directory_path(
                config.output_dir, must_exist=False, create_if_missing=False
            )

        # Create session with consistent configuration
        session_config = SessionConfig(
            default_template=template,
            default_format="pdf",
            auto_open=config.open_after,
            preview_mode=config.preview,
            output_dir=Path(config.output_dir) if config.output_dir else None,
            session_metadata=config_overrides,
        )

        with ResumeSession(
            data_dir=config.data_dir, paths=config.paths, config=session_config
        ) as session:
            if config.name:
                # Generate single resume
                resume = session.resume(config.name)
                if config_overrides:
                    resume = resume.with_config(**config_overrides)
                return resume.to_pdf(open_after=config.open_after)
            else:
                # Generate multiple resumes
                return session.generate_all(
                    format="pdf",
                    pattern=config.pattern,
                    open_after=config.open_after,
                    **config_overrides,
                )

    except Exception as exc:
        if isinstance(
            exc, (GenerationError, ValidationError, ConfigurationError, FileSystemError)
        ):
            raise
        raise GenerationError(
            f"Failed to generate PDFs: {exc}", format_type="pdf"
        ) from exc


def generate_pdf(
    config: GenerationConfig,
    **config_overrides: Any,
) -> GenerationResult | BatchGenerationResult:
    """Generate PDF resumes using a configuration object.

    Args:
        config: Configuration describing what to render and where to write output.
        **config_overrides: Keyword overrides applied to the resume configuration.

    Returns:
        A generation result for a single resume or a batch when multiple
        files are rendered.

    Raises:
        ConfigurationError: Raised on invalid path configuration.
        GenerationError: Raised when PDF rendering fails.
        ValidationError: Raised when resume data fails validation.
        FileSystemError: Raised on filesystem errors during rendering.

    Examples:
        Generate all resumes in a directory::

            cfg = GenerationConfig(data_dir="my_resumes")
            results = generate_pdf(cfg)

        Render a single resume with overrides::

            cfg = GenerationConfig(
                name="casey",
                template="resume_with_bars",
                open_after=True,
            )
            result = generate_pdf(cfg, theme_color="#0066CC")

    """
    return _generate_pdf_impl(config, **config_overrides)


def generate_html(
    config: GenerationConfig,
    **config_overrides: Any,
) -> GenerationResult | BatchGenerationResult:
    """Generate HTML resumes using a configuration object.

    Args:
        config: Configuration describing what to render and where to write output.
        **config_overrides: Keyword overrides applied to the resume configuration.

    Returns:
        A generation result for a single resume or a batch when multiple
        files are rendered.

    Raises:
        ConfigurationError: Raised on invalid path configuration.
        GenerationError: Raised when HTML rendering fails.
        ValidationError: Raised when resume data fails validation.
        FileSystemError: Raised on filesystem errors during rendering.

    Examples:
        Generate HTML with preview enabled::

            cfg = GenerationConfig(data_dir="my_resumes", preview=True)
            results = generate_html(cfg)

        Render a single resume in the browser of choice::

            cfg = GenerationConfig(
                name="casey",
                template="resume_no_bars",
                browser="firefox",
            )
            result = generate_html(cfg)

    """
    time.time()

    try:
        # Create session with consistent configuration
        session_config = SessionConfig(
            default_template=config.template,
            default_format="html",
            auto_open=config.open_after,
            preview_mode=config.preview,
            output_dir=Path(config.output_dir) if config.output_dir else None,
            session_metadata=config_overrides,
        )

        with ResumeSession(
            data_dir=config.data_dir, paths=config.paths, config=session_config
        ) as session:
            if config.name:
                # Generate single resume
                resume = session.resume(config.name)
                if config_overrides:
                    resume = resume.with_config(**config_overrides)
                return resume.to_html(
                    open_after=config.open_after,
                    browser=config.browser,
                )
            else:
                # Generate multiple resumes
                return session.generate_all(
                    format="html",
                    pattern=config.pattern,
                    open_after=config.open_after,
                    **config_overrides,
                )

    except Exception as exc:
        if isinstance(
            exc, (GenerationError, ValidationError, ConfigurationError, FileSystemError)
        ):
            raise
        raise GenerationError(
            f"Failed to generate HTML: {exc}",
            format_type="html",
        ) from exc


def generate_all(
    config: GenerationConfig,
    **config_overrides: Any,
) -> dict[str, GenerationResult | BatchGenerationResult]:
    """Generate resumes in all specified formats.

    This function provides a convenient way to generate resumes in multiple formats
    with a single call, maintaining consistent parameter patterns.

    Args:
        config: Configuration describing what to render and which formats to include.
        **config_overrides: Keyword overrides applied to individual resume renders.

    Returns:
        Dictionary mapping format names to GenerationResult or BatchGenerationResult

    Raises:
        ValueError: If any requested format is not supported.
        ConfigurationError: If path configuration is invalid.
        GenerationError: If generation fails for any format.

    Examples:
        # Generate all resumes in both PDF and HTML formats
        results = generate_all("my_resumes")

        # Generate specific resume in multiple formats
        results = generate_all(
            GenerationConfig(
                name="my_resume",
                formats=["pdf", "html"],
                template="professional",
            )
        )

    """
    # Validate and normalize formats
    formats = config.formats or ["pdf", "html"]
    normalized_formats: list[str] = []
    for fmt in formats:
        normalized_formats.append(validate_format(fmt, param_name="format"))

    if config.template:
        template = validate_template_name(config.template)
    else:
        template = None

    if config.data_dir:
        validate_directory_path(config.data_dir, must_exist=True)

    if config.output_dir:
        validate_directory_path(
            config.output_dir,
            must_exist=False,
            create_if_missing=False,
        )

    results: dict[str, GenerationResult | BatchGenerationResult] = {}

    try:
        # Create session for consistent configuration
        session_config = SessionConfig(
            default_template=template,
            default_format=normalized_formats[0]
            if normalized_formats
            else DEFAULT_FORMAT,
            auto_open=config.open_after,
            preview_mode=config.preview,
            output_dir=Path(config.output_dir) if config.output_dir else None,
            session_metadata=config_overrides,
        )

        with ResumeSession(
            data_dir=config.data_dir, paths=config.paths, config=session_config
        ) as session:
            for format_type in normalized_formats:
                if format_type == "pdf":
                    results["pdf"] = (
                        session.generate_all(
                            format="pdf",
                            pattern=config.pattern,
                            open_after=config.open_after,
                            **config_overrides,
                        )
                        if not config.name
                        else session.resume(config.name).to_pdf(
                            open_after=config.open_after,
                        )
                    )

                elif format_type == "html":
                    results["html"] = (
                        session.generate_all(
                            format="html",
                            pattern=config.pattern,
                            open_after=config.open_after,
                            **config_overrides,
                        )
                        if not config.name
                        else session.resume(config.name).to_html(
                            open_after=config.open_after,
                            browser=config.browser,
                        )
                    )

    except Exception as exc:
        if isinstance(
            exc, (GenerationError, ValidationError, ConfigurationError, FileSystemError)
        ):
            raise
        raise GenerationError(
            f"Failed to generate resumes: {exc}",
            format_type=", ".join(formats),
        ) from exc

    return results


def generate_resume(
    config: GenerationConfig,
    **config_overrides: Any,
) -> GenerationResult:
    """Generate a single resume with pandas-style function signature.

    This function follows pandas naming conventions for single-item operations
    and provides a simple, consistent interface.

    Args:
        config: Configuration describing the resume to render.
        **config_overrides: Keyword overrides applied to the resume configuration.

    Returns:
        GenerationResult with metadata and operations

    Examples:
        # Simple generation
        result = generate_resume(GenerationConfig(name="my_resume"))

        # With template and output path
        result = generate_resume(
            GenerationConfig(
                name="my_resume",
                format="pdf",
                template="professional",
                output_path="output/my_resume.pdf",
            )
        )

    """
    # Validate and normalize format
    format = validate_format(config.format, param_name="format")

    # Create config with specific format and handle output_path
    specific_config = GenerationConfig(
        data_dir=config.data_dir,
        output_dir=(
            Path(config.output_path).parent if config.output_path else config.output_dir
        ),
        output_path=config.output_path,
        paths=config.paths,
        template=config.template,
        format=format,
        open_after=config.open_after,
        preview=config.preview,
        name=config.name,
        pattern=config.pattern,
        browser=config.browser,
        formats=config.formats,
    )

    # Use appropriate generation function
    if format == "pdf":
        pdf_result = generate_pdf(specific_config, **config_overrides)
        if isinstance(pdf_result, GenerationResult):
            return pdf_result
        raise TypeError("generate_pdf returned batch result for single resume")

    html_result = generate_html(specific_config, **config_overrides)
    if isinstance(html_result, GenerationResult):
        return html_result
    raise TypeError("generate_html returned batch result for single resume")


__all__ = [
    "GenerationConfig",
    "generate_pdf",
    "generate_html",
    "generate_all",
    "generate_resume",
]
