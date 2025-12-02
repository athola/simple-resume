"""Lazy-loaded generation functions for optimal import performance.

This module provides thin wrappers around the core generation functions
with lazy loading to reduce startup memory footprint.
"""

from __future__ import annotations

import importlib
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any

from simple_resume.core.models import GenerationConfig


class _LazyRuntimeLoader:
    """Lazy loader for runtime generation functions."""

    def __init__(self) -> None:
        self._core: ModuleType | None = None
        self._loaded = False

    def _load_core(self) -> ModuleType:
        """Load runtime module if not already loaded."""
        if not self._loaded:
            self._core = importlib.import_module(".generate", package=__package__)
            self._loaded = True
        # _core is set when _loaded is True
        return self._core  # type: ignore[return-value]

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
def _get_lazy_core() -> _LazyRuntimeLoader:
    """Return a shared lazy loader instance without module-level globals."""
    return _LazyRuntimeLoader()


def generate_pdf(
    config: GenerationConfig,
    **config_overrides: Any,
) -> Any:
    """Generate PDF resumes using a configuration object (lazy-loaded wrapper)."""
    return _get_lazy_core().generate_pdf(config, **config_overrides)


def generate_html(
    config: GenerationConfig,
    **config_overrides: Any,
) -> Any:
    """Generate HTML resumes using a configuration object (lazy-loaded wrapper)."""
    return _get_lazy_core().generate_html(config, **config_overrides)


def generate_all(
    config: GenerationConfig,
    **config_overrides: Any,
) -> Any:
    """Generate resumes in all specified formats (lazy-loaded wrapper)."""
    return _get_lazy_core().generate_all(config, **config_overrides)


def generate_resume(
    config: GenerationConfig,
    **config_overrides: Any,
) -> Any:
    """Generate a resume in a specific format (lazy-loaded wrapper)."""
    return _get_lazy_core().generate_resume(config, **config_overrides)


def generate(
    source: str | Path,
    options: Any | None = None,
    **overrides: Any,
) -> Any:
    """Render one or more formats for the same source (lazy-loaded wrapper)."""
    return _get_lazy_core().generate(source, options, **overrides)


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
    return _get_lazy_core().preview(
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
