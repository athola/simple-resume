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

Refer to ``docs/reference.md`` for a complete API map and stability labels.
"""

from __future__ import annotations

# Exception hierarchy
from simple_resume.core.exceptions import (
    ConfigurationError,
    FileSystemError,
    GenerationError,
    PaletteError,
    SessionError,
    SimpleResumeError,
    TemplateError,
    ValidationError,
)

# Core classes (data models only - no I/O methods)
from simple_resume.core.models import GenerationConfig, RenderPlan, ResumeConfig

# Shell layer I/O operations - these are the primary generation functions
from simple_resume.shell.resume_extensions import (
    generate as resume_generate,
)
from simple_resume.shell.resume_extensions import (
    to_html,
    to_pdf,
)

# Public API namespaces - higher-level generation functions
from .shell.generate import (
    generate,
    generate_all,
    generate_html,
    generate_pdf,
    generate_resume,
    preview,
)

# Rich result objects (lazy-loaded)
from .shell.runtime.lazy_import import (
    lazy_BatchGenerationResult as BatchGenerationResult,
)

# Session management (lazy-loaded)
from .shell.runtime.lazy_import import (
    lazy_create_session as create_session,
)
from .shell.runtime.lazy_import import (
    lazy_GenerationMetadata as GenerationMetadata,
)
from .shell.runtime.lazy_import import (
    lazy_GenerationResult as GenerationResult,
)
from .shell.runtime.lazy_import import (
    lazy_ResumeSession as ResumeSession,
)
from .shell.runtime.lazy_import import (
    lazy_SessionConfig as SessionConfig,
)

# Version
__version__ = "0.1.0"

# Public API exports - organized by functionality
__all__ = [
    "__version__",
    # Core models (data only)
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
    # Shell layer I/O functions
    "to_pdf",
    "to_html",
    "resume_generate",
    # Convenience helpers
    "generate",
    "preview",
]
