"""High-level resume generation module.

This module provides a clean, organized interface for generating resumes
in various formats. It offers both standard (eager) and lazy-loading
implementations to optimize for different use cases.

The module is organized as follows:
- `core`: Standard generation functions with immediate imports
- `lazy`: Lazy-loading versions for better import performance
- Direct exports provide the most commonly used functions
"""

from __future__ import annotations

# Also make core versions available for those who need them
from . import core

# Re-export lazy loading versions as default (better performance)
from .lazy import (
    generate,
    generate_all,
    generate_html,
    generate_pdf,
    generate_resume,
    preview,
)

# For backward compatibility and direct access
__all__ = [
    # Public API functions (lazy-loaded by default)
    "generate",
    "generate_all",
    "generate_html",
    "generate_pdf",
    "generate_resume",
    "preview",
    # Module access
    "core",
    "lazy",
]
