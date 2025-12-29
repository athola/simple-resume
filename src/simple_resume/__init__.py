#!/usr/bin/env python3
"""Define the Simple Resume public API.

Symbols listed in `:data:simple_resume.__all__` are covered by the
stability contract, mirroring pandas' curated ``pandas.api`` surface.
Other components (utility helpers, palette plumbing, rendering shell, etc.)
reside under `:mod:simple_resume.core` and `:mod:simple_resume.shell`
and may change without notice. Import from those modules only if prepared
to track upstream changes.

High-level categories include:

* **Core models** – `:class:Resume`, `:class:ResumeConfig`, and
  `:class:RenderPlan` represent resumes and render plans.
* **Sessions & results** – `:class:ResumeSession`, `:class:SessionConfig`,
  `:class:GenerationResult`, and `:class:BatchGenerationResult`.
* **Generation helpers** – ``generate_pdf/html/all/resume`` plus new
  convenience wrappers `:func:generate` and `:func:preview` for one-liner
  workflows, similar to ``requests`` verb helpers.
* **FCIS Architecture** – Functional core in `:mod:simple_resume.core`
  (e.g., `:mod:simple_resume.core.colors`) provides pure functions,
  while shell layer handles I/O and side effects.

Refer to ``README.md`` and ``wiki/architecture/ADR003-api-surface-design.md``
for the API map and stability notes.
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
from simple_resume.core.models import (
    GenerationConfig,
    RenderPlan,
    ResumeConfig,
    ValidationResult,
)
from simple_resume.core.resume import Resume

# Public API namespaces - higher-level generation functions
from simple_resume.shell.generate import (
    generate,
    generate_all,
    generate_html,
    generate_pdf,
    generate_resume,
    preview,
)

# Shell layer I/O operations - these are the primary generation functions
from simple_resume.shell.resume_extensions import (
    generate as resume_generate,
)
from simple_resume.shell.resume_extensions import (
    to_html,
    to_pdf,
)

# Rich result objects (lazy-loaded)
from simple_resume.shell.runtime.lazy_import import (
    lazy_BatchGenerationResult as BatchGenerationResult,
)

# Session management (lazy-loaded)
from simple_resume.shell.runtime.lazy_import import (
    lazy_create_session as create_session,
)
from simple_resume.shell.runtime.lazy_import import (
    lazy_GenerationMetadata as GenerationMetadata,
)
from simple_resume.shell.runtime.lazy_import import (
    lazy_GenerationResult as GenerationResult,
)
from simple_resume.shell.runtime.lazy_import import (
    lazy_ResumeSession as ResumeSession,
)
from simple_resume.shell.runtime.lazy_import import (
    lazy_SessionConfig as SessionConfig,
)

# Version
__version__ = "0.1.5"

# Public API exports - organized by functionality
__all__ = [
    "__version__",
    # Core models (data only)
    "Resume",
    "ResumeConfig",
    "RenderPlan",
    "ValidationResult",
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
