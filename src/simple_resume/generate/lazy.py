"""Lazy-loaded generation functions for optimal import performance.

This module provides thin wrappers around the core generation functions
with lazy imports to reduce startup memory footprint.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core.models import GenerationConfig


# Lazy imports - these will only be imported when functions are called
def _lazy_import_core() -> Any:
    """Lazy import core generation functions."""
    from . import core

    return core


def generate_pdf(
    config: GenerationConfig,
    **config_overrides: Any,
) -> Any:
    """Generate PDF resumes using a configuration object (lazy-loaded wrapper)."""
    core = _lazy_import_core()
    return core.generate_pdf(config, **config_overrides)


def generate_html(
    config: GenerationConfig,
    **config_overrides: Any,
) -> Any:
    """Generate HTML resumes using a configuration object (lazy-loaded wrapper)."""
    core = _lazy_import_core()
    return core.generate_html(config, **config_overrides)


def generate_all(
    config: GenerationConfig,
    **config_overrides: Any,
) -> Any:
    """Generate resumes in all specified formats (lazy-loaded wrapper)."""
    core = _lazy_import_core()
    return core.generate_all(config, **config_overrides)


def generate_resume(
    config: GenerationConfig,
    **config_overrides: Any,
) -> Any:
    """Generate a resume in a specific format (lazy-loaded wrapper)."""
    core = _lazy_import_core()
    return core.generate_resume(config, **config_overrides)


def generate(
    source: str | Path,
    options: Any | None = None,
    **overrides: Any,
) -> Any:
    """Render one or more formats for the same source (lazy-loaded wrapper)."""
    core = _lazy_import_core()
    return core.generate(source, options, **overrides)


def preview(
    source: str | Path,
    *,
    data_dir: str | Path | None = None,
    template: str | None = None,
    browser: str | None = None,
    open_after: bool = True,
    **overrides: Any,
) -> Any:
    """Render a single resume to HTML with preview defaults (lazy-loaded wrapper)."""
    core = _lazy_import_core()
    return core.preview(
        source,
        data_dir=data_dir,
        template=template,
        browser=browser,
        open_after=open_after,
        **overrides,
    )


__all__ = [
    "generate_pdf",
    "generate_html",
    "generate_all",
    "generate_resume",
    "generate",
    "preview",
]
