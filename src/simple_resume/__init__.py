#!/usr/bin/env python3
"""Define the Simple Resume public API.

Symbols listed in `:data:simple_resume.__all__` are covered by the
stability contract, mirroring pandas' curated ``pandas.api`` surface.
Other components (utility helpers, palette plumbing, rendering shell, etc.)
reside under `:mod:simple_resume.internal` and may change without notice.
Import from ``simple_resume.internal`` only if prepared to track upstream changes.

High-level categories include:

* **Core models** – `:class:Resume`, `:class:ResumeConfig`, and
  `:class:RenderPlan` represent resumes and render plans.
* **Sessions & results** – `:class:ResumeSession`, `:class:SessionConfig`,
  `:class:GenerationResult`, and `:class:BatchGenerationResult`.
* **Generation helpers** – ``generate_pdf/html/all/resume`` plus new
  convenience wrappers `:func:generate` and `:func:preview` for one-liner
  workflows, similar to ``requests`` verb helpers.
* **Curated API namespaces** – Modules under `:mod:simple_resume.api`
  (e.g., `:mod:simple_resume.api.colors`) mirror ``pandas.api`` by
  re-exporting stable helper families.

Refer to ``docs/reference.md`` for a complete API map, stability labels, and
deprecation policy.
"""

from __future__ import annotations

# Public API namespaces
from . import api

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
