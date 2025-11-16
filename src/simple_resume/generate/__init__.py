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

from typing import Any, Callable, TypeVar, cast

# Also make core versions available for those who need them
from . import core, lazy

TCallable = TypeVar("TCallable", bound=Callable[..., Any])


def _with_namespaces(func: TCallable) -> TCallable:
    """Attach helpful module references to exported callables."""
    namespace_func = cast(Any, func)
    namespace_func.core = core
    namespace_func.lazy = lazy
    return func


# Re-export lazy loading versions as default (better performance)
generate = _with_namespaces(lazy.generate)
generate_all = _with_namespaces(lazy.generate_all)
generate_html = _with_namespaces(lazy.generate_html)
generate_pdf = _with_namespaces(lazy.generate_pdf)
generate_resume = _with_namespaces(lazy.generate_resume)
preview = _with_namespaces(lazy.preview)

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
