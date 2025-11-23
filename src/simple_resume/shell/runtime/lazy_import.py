"""Lazy loading utilities for optimizing import performance.

This module provides utilities to defer heavy imports until actually needed,
reducing initial memory footprint and improving startup performance.
"""

from __future__ import annotations

import importlib
from functools import lru_cache
from typing import Any, Callable, TypeVar, cast

T = TypeVar("T")


class LazyModule:
    """A module that loads on first attribute access."""

    def __init__(self, module_name: str) -> None:
        """Initialize lazy module.

        Args:
            module_name: Full module path to import when needed

        """
        self._module_name = module_name
        self._module: Any = None
        self._loaded = False

    def _load(self) -> Any:
        """Load the module if not already loaded."""
        if not self._loaded:
            self._module = importlib.import_module(self._module_name)
            self._loaded = True
        return self._module

    def __getattr__(self, name: str) -> Any:
        """Get attribute from the lazily loaded module."""
        module = self._load()
        return getattr(module, name)

    def __dir__(self) -> list[str]:
        """Return directory listing of the module when loaded."""
        module = self._load()
        return dir(module)


class LazyFunction:
    """A function that loads its implementation on first call."""

    def __init__(self, module_path: str, function_name: str) -> None:
        """Initialize lazy function.

        Args:
            module_path: Full module path containing the function
            function_name: Name of the function to lazy-load

        """
        self._module_path = module_path
        self._function_name = function_name
        self._function: Callable[..., Any] | None = None
        self._loaded = False

    def _load(self) -> Callable[..., Any]:
        """Load the function if not already loaded."""
        if not self._loaded:
            module = importlib.import_module(self._module_path)
            self._function = getattr(module, self._function_name)
            self._loaded = True
        # After loading, _function is guaranteed to be set
        return cast(Callable[..., Any], self._function)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the lazily loaded function."""
        function = self._load()
        return function(*args, **kwargs)


@lru_cache(maxsize=128)
def lazy_import(module_path: str) -> LazyModule:
    """Create a cached lazy module instance.

    Args:
        module_path: Full module path to import lazily

    Returns:
        LazyModule instance that loads on first access

    """
    return LazyModule(module_path)


@lru_cache(maxsize=64)
def lazy_function(module_path: str, function_name: str) -> LazyFunction:
    """Create a cached lazy function instance.

    Args:
        module_path: Full module path containing the function
        function_name: Name of the function to lazy-load

    Returns:
        LazyFunction instance that loads on first call

    """
    return LazyFunction(module_path, function_name)


# Common lazy-loaded modules
_lazy_session = lazy_import("simple_resume.shell.session")
_lazy_result = lazy_import("simple_resume.core.result")
_lazy_validation = lazy_import("simple_resume.core.validation")


# Public lazy API functions
def lazy_create_session(*args: Any, **kwargs: Any) -> Any:
    """Lazily loaded create_session function."""
    return _lazy_session.create_session(*args, **kwargs)


def lazy_ResumeSession(*args: Any, **kwargs: Any) -> Any:
    """Lazily loaded ResumeSession class."""
    return _lazy_session.ResumeSession(*args, **kwargs)


def lazy_SessionConfig(*args: Any, **kwargs: Any) -> Any:
    """Lazily loaded SessionConfig class."""
    return _lazy_session.SessionConfig(*args, **kwargs)


def lazy_GenerationResult(*args: Any, **kwargs: Any) -> Any:
    """Lazily loaded GenerationResult class."""
    return _lazy_result.GenerationResult(*args, **kwargs)


def lazy_BatchGenerationResult(*args: Any, **kwargs: Any) -> Any:
    """Lazily loaded BatchGenerationResult class."""
    return _lazy_result.BatchGenerationResult(*args, **kwargs)


def lazy_GenerationMetadata(*args: Any, **kwargs: Any) -> Any:
    """Lazily loaded GenerationMetadata class."""
    return _lazy_result.GenerationMetadata(*args, **kwargs)


def lazy_validate_directory_path(*args: Any, **kwargs: Any) -> Any:
    """Lazily loaded validate_directory_path function."""
    return _lazy_validation.validate_directory_path(*args, **kwargs)


def lazy_validate_format(*args: Any, **kwargs: Any) -> Any:
    """Lazily loaded validate_format function."""
    return _lazy_validation.validate_format(*args, **kwargs)


def lazy_validate_template_name(*args: Any, **kwargs: Any) -> Any:
    """Lazily loaded validate_template_name function."""
    return _lazy_validation.validate_template_name(*args, **kwargs)


__all__ = [
    "LazyModule",
    "LazyFunction",
    "lazy_import",
    "lazy_function",
    "lazy_create_session",
    "lazy_ResumeSession",
    "lazy_SessionConfig",
    "lazy_GenerationResult",
    "lazy_BatchGenerationResult",
    "lazy_validate_directory_path",
    "lazy_validate_format",
    "lazy_validate_template_name",
]
