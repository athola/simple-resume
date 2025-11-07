#!/usr/bin/env python3
"""Simple Resume public API.

Only the symbols listed in :data:`simple_resume.__all__` are covered by the
stability contract—this matches the way pandas exposes its curated
``pandas.api`` surface. Everything else (utility helpers, palette plumbing, the
rendering shell, etc.) lives under :mod:`simple_resume.internal` and may change
without notice. Import from ``simple_resume.internal`` only when you are
prepared to track upstream changes.

High-level categories:

* **Core models** – :class:`Resume`, :class:`ResumeConfig`, and
  :class:`RenderPlan` for representing resumes and render plans.
* **Sessions & results** – :class:`ResumeSession`, :class:`SessionConfig`,
  :class:`GenerationResult`, and :class:`BatchGenerationResult`.
* **Generation helpers** – ``generate_pdf/html/all/resume`` plus the new
  convenience wrappers :func:`generate` and :func:`preview` for one-liner
  workflows similar to the verb helpers that ``requests`` provides.

Refer to ``docs/reference.md`` for a complete API map, stability labels, and
deprecation policy.
"""

from __future__ import annotations

# Core classes
from .core.resume import RenderPlan, Resume, ResumeConfig

# Exception hierarchy
from .exceptions import (
    ConfigurationError,
    FileSystemError,
    GenerationError,
    PaletteError,
    SessionError,
    SimpleResumeError,
    TemplateError,
    ValidationError,
)

# New unified generation API
from .generation import (
    GenerationConfig,
    generate,
    generate_all,
    generate_html,
    generate_pdf,
    generate_resume,
    preview,
)

# Rich result objects
from .result import BatchGenerationResult, GenerationMetadata, GenerationResult

# Session management
from .session import ResumeSession, SessionConfig, create_session

# Utility functions
from .utilities import (
    calculate_luminance,
    calculate_text_color,
    get_content,
    normalize_config,
    render_markdown_content,
    validate_config,
)

# Version
__version__ = "0.1.0"

# Public API exports - organized by functionality
__all__ = [
    "__version__",
    # Core models
    "Resume",
    "ResumeConfig",
    "RenderPlan",
    # Exceptions
    "SimpleResumeError",
    "ValidationError",
    "ConfigurationError",
    "TemplateError",
    "GenerationError",
    "PaletteError",
    "FileSystemError",
    "SessionError",
    # Results & sessions
    "GenerationResult",
    "GenerationMetadata",
    "BatchGenerationResult",
    "ResumeSession",
    "SessionConfig",
    "create_session",
    # Generation primitives
    "GenerationConfig",
    "generate_pdf",
    "generate_html",
    "generate_all",
    "generate_resume",
    # Convenience helpers
    "generate",
    "preview",
]
