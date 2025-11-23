"""High-level resume generation module in shell layer.

This module provides a clean, organized interface for generating resumes
in various formats. It offers both standard (eager) and lazy-loading
implementations to optimize for different use cases.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar, cast

from . import core as core_module
from . import lazy as lazy_module

TCallable = TypeVar("TCallable", bound=Callable[..., Any])


def _with_namespaces(func: TCallable) -> TCallable:
    """Attach helpful module references to exported callables."""
    namespace_func = cast(Any, func)
    namespace_func.core = core_module
    namespace_func.lazy = lazy_module
    return func


# Re-export lazy loading versions as default (better performance)
generate = _with_namespaces(lazy_module.generate)
generate_all = _with_namespaces(lazy_module.generate_all)
generate_html = _with_namespaces(lazy_module.generate_html)
generate_pdf = _with_namespaces(lazy_module.generate_pdf)
generate_resume = _with_namespaces(lazy_module.generate_resume)
preview = _with_namespaces(lazy_module.preview)

# Re-export configuration types
GenerateOptions = core_module.GenerateOptions

__all__ = [
    "generate",
    "generate_all",
    "generate_html",
    "generate_pdf",
    "generate_resume",
    "preview",
    "GenerateOptions",
    "core_module",
    "lazy_module",
]
