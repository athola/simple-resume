"""Dependency injection container and interfaces for improved testability.

This module introduces dependency injection patterns to reduce coupling between
Session and Resume classes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from simple_resume.core.paths import Paths
from simple_resume.core.resume import Resume


class SessionConfigProtocol(Protocol):
    """Minimal session config contract needed by the core."""

    default_template: str | None
    default_palette: str | None
    preview_mode: bool


class NullSessionConfig:
    """Fallback config used when no SessionConfig is supplied."""

    default_template: str | None = None
    default_palette: str | None = None
    preview_mode: bool = False


class ResumeLoader(Protocol):
    """Protocol for loading resume instances."""

    def load_resume(
        self,
        name: str,
        *,
        paths: Paths | None = None,
        transform_markdown: bool = True,
    ) -> Resume:
        """Load a resume by name with given configuration."""
        ...


class ResumeCache(Protocol):
    """Protocol for caching resume instances."""

    def get_resume(self, key: str) -> Resume | None:
        """Get a resume from cache."""
        ...

    def put_resume(self, key: str, resume: Resume) -> None:
        """Put a resume into cache."""
        ...

    def invalidate_resume(self, key: str | None = None) -> None:
        """Invalidate cached resume(s)."""
        ...

    def clear_cache(self) -> None:
        """Clear all cached resumes."""
        ...

    def get_cache_keys(self) -> list[str]:
        """Get list of cached resume keys."""
        ...

    def get_cache_size(self) -> int:
        """Get number of cached resumes."""
        ...

    def get_memory_usage(self) -> int:
        """Get estimated memory usage of cached resumes in bytes."""
        ...


class ResumeConfigurator(Protocol):
    """Protocol for configuring resume instances."""

    def configure_resume(self, resume: Resume, config: SessionConfigProtocol) -> Resume:
        """Apply session configuration to a resume."""
        ...


class DefaultResumeLoader:
    """Default implementation of ResumeLoader using Resume.read_yaml."""

    def load_resume(
        self,
        name: str,
        *,
        paths: Paths | None = None,
        transform_markdown: bool = True,
    ) -> Resume:
        """Load resume using Resume.read_yaml method."""
        return Resume.read_yaml(
            name=name,
            paths=paths,
            transform_markdown=transform_markdown,
        )


class MemoryResumeCache:
    """In-memory implementation of ResumeCache."""

    def __init__(self) -> None:
        """Initialize an empty in-memory cache."""
        self._cache: dict[str, Resume] = {}

    def get_resume(self, key: str) -> Resume | None:
        """Get a resume from cache."""
        return self._cache.get(key)

    def put_resume(self, key: str, resume: Resume) -> None:
        """Put a resume into cache."""
        self._cache[key] = resume

    def invalidate_resume(self, key: str | None = None) -> None:
        """Invalidate cached resume(s)."""
        if key is None:
            self._cache.clear()
        else:
            self._cache.pop(key, None)

    def clear_cache(self) -> None:
        """Clear all cached resumes."""
        self._cache.clear()

    def get_cache_keys(self) -> list[str]:
        """Get list of cached resume keys."""
        return list(self._cache.keys())

    def get_cache_size(self) -> int:
        """Get number of cached resumes."""
        return len(self._cache)

    def get_memory_usage(self) -> int:
        """Get estimated memory usage of cached resumes in bytes."""
        return sum(len(str(resume._data)) for resume in self._cache.values())


class DefaultResumeConfigurator:
    """Default implementation of ResumeConfigurator."""

    def configure_resume(self, resume: Resume, config: SessionConfigProtocol) -> Resume:
        """Apply session configuration to a resume."""
        result = resume

        # Apply default template if specified
        if config.default_template:
            result = result.with_template(config.default_template)

        # Apply default palette if specified
        if config.default_palette:
            result = result.with_palette(config.default_palette)

        # Apply preview mode if enabled
        if config.preview_mode:
            result = result.preview()

        return result


class ResumeRepository:
    """Repository for managing resume loading and caching."""

    def __init__(
        self,
        loader: ResumeLoader,
        cache: ResumeCache,
        configurator: ResumeConfigurator,
    ) -> None:
        """Initialize repository with dependencies."""
        self._loader = loader
        self._cache = cache
        self._configurator = configurator

    def get_resume(
        self,
        name: str,
        paths: Paths | None = None,
        use_cache: bool = True,
        config: SessionConfigProtocol | None = None,
    ) -> Resume:
        """Get a resume, loading from cache or file as needed."""
        cache_key = name

        # Try cache first
        if use_cache and (cached_resume := self._cache.get_resume(cache_key)):
            # Apply configuration to cached resume
            merged_config = config or NullSessionConfig()
            return self._configurator.configure_resume(cached_resume, merged_config)

        # Load from file
        resume = self._loader.load_resume(name, paths=paths)

        # Apply configuration
        if config:
            resume = self._configurator.configure_resume(resume, config)

        # Cache the result
        if use_cache:
            self._cache.put_resume(cache_key, resume)

        return resume

    def invalidate_cache(self, name: str | None = None) -> None:
        """Invalidate cached resume(s)."""
        self._cache.invalidate_resume(name)

    def clear_cache(self) -> None:
        """Clear all cached resumes."""
        self._cache.clear_cache()

    def get_cache_info(self) -> dict[str, Any]:
        """Return information about cached resume data.

        Returns:
            Dictionary with cache statistics.

        """
        return {
            "cached_resumes": self._cache.get_cache_keys(),
            "cache_size": self._cache.get_cache_size(),
            "memory_usage_estimate": self._cache.get_memory_usage(),
        }

    def get_cache_keys(self) -> list[str]:
        """Get list of cached resume keys."""
        return self._cache.get_cache_keys()

    def get_cache_size(self) -> int:
        """Get number of cached resumes."""
        return self._cache.get_cache_size()

    def get_memory_usage(self) -> int:
        """Get estimated memory usage of cached resumes in bytes."""
        return self._cache.get_memory_usage()


@dataclass
class DIContainer:
    """Dependency injection container for creating configured objects."""

    resume_loader: ResumeLoader = field(default_factory=DefaultResumeLoader)
    resume_cache: ResumeCache = field(default_factory=MemoryResumeCache)
    resume_configurator: ResumeConfigurator = field(
        default_factory=DefaultResumeConfigurator
    )

    def create_resume_repository(self) -> ResumeRepository:
        """Create a ResumeRepository with configured dependencies."""
        return ResumeRepository(
            loader=self.resume_loader,
            cache=self.resume_cache,
            configurator=self.resume_configurator,
        )
