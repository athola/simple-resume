"""Manage sessions for simple-resume operations.

This module provides `ResumeSession` for managing consistent configuration
across multiple resume operations, similar to `requests.Session`.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import replace as dataclass_replace
from pathlib import Path
from types import TracebackType
from typing import Any

from simple_resume.core.constants import OutputFormat
from simple_resume.core.dependencies import (
    DefaultResumeConfigurator,
    DefaultResumeLoader,
    DIContainer,
    MemoryResumeCache,
)
from simple_resume.core.exceptions import ConfigurationError, SessionError
from simple_resume.core.file_operations import find_yaml_files
from simple_resume.core.paths import Paths
from simple_resume.core.result import BatchGenerationResult, GenerationResult
from simple_resume.core.resume import Resume
from simple_resume.shell.config import resolve_paths
from simple_resume.shell.resume_extensions import to_html, to_pdf
from simple_resume.shell.session.config import SessionConfig


class ResumeSession:
    """Manage resume operations with consistent configuration.

    Similar to `requests.Session`, `ResumeSession` provides:
    - Consistent configuration across operations.
    - State management for path resolution.
    - Batch operations support.
    - Resource cleanup.

    Usage:
        with ResumeSession(data_dir="my_resumes") as session:
            resume = session.resume("my_resume")
            result = resume.to_pdf(open_after=True)
            session.generate_all(format="html")
    """

    def __init__(
        self,
        data_dir: str | Path | None = None,
        *,
        paths: Paths | None = None,
        config: SessionConfig | None = None,
        **path_overrides: str | Path,
    ) -> None:
        """Initialize a `ResumeSession`.

        Args:
            data_dir: Base data directory containing input/output folders.
            paths: Pre-resolved paths object.
            config: Session configuration.
            **path_overrides: Path configuration overrides.

        Raises:
            `ConfigurationError`: If path configuration is invalid.
            `SessionError`: If session initialization fails.

        """
        self._session_id = str(uuid.uuid4())
        self._created_at = time.time()
        self._is_active = True

        # Configure paths
        if path_overrides and paths is not None:
            raise ConfigurationError("Provide either paths or path_overrides, not both")

        if paths is not None:
            self._paths = paths
        else:
            try:
                self._paths = resolve_paths(data_dir, **path_overrides)
            except Exception as exc:
                raise ConfigurationError(f"Failed to resolve paths: {exc}") from exc

        # Configure session settings
        self._config = config or SessionConfig()
        if self._config.paths is None:
            self._config.paths = self._paths

        # Apply output directory override if specified
        if self._config.output_dir:
            self._paths = dataclass_replace(self._paths, output=self._config.output_dir)
            self._config.paths = self._paths

        # Initialize dependency injection
        container = DIContainer(
            resume_loader=DefaultResumeLoader(),
            resume_cache=MemoryResumeCache(),
            resume_configurator=DefaultResumeConfigurator(),
        )
        self._repository = container.create_resume_repository()

        # Track session statistics
        self._operation_count = 0
        self._generation_times: list[float] = []

    @property
    def session_id(self) -> str:
        """Return the unique session identifier."""
        return self._session_id

    @property
    def paths(self) -> Paths:
        """Return the resolved paths for this session."""
        return self._paths

    @property
    def config(self) -> SessionConfig:
        """Return the session configuration."""
        return self._config

    @property
    def is_active(self) -> bool:
        """Check if the session is currently active."""
        return self._is_active

    @property
    def operation_count(self) -> int:
        """Return the number of operations performed in this session."""
        return self._operation_count

    @property
    def average_generation_time(self) -> float:
        """Return the average generation time for this session."""
        if not self._generation_times:
            return 0.0
        return sum(self._generation_times) / len(self._generation_times)

    def resume(self, name: str, *, use_cache: bool = True) -> Resume:
        """Load a resume within this session context.

        Args:
            name: Resume identifier without extension.
            use_cache: Whether to use cached resume data if available.

        Returns:
            `Resume` instance loaded with session configuration.

        Raises:
            `SessionError`: If the session is not active or resume loading fails.

        """
        if not self._is_active:
            raise SessionError(
                "Cannot load resume - session is not active",
                session_id=self._session_id,
            )

        try:
            # Use dependency injection for resume loading
            resume = self._repository.get_resume(
                name=name,
                paths=self._paths,
                use_cache=use_cache,
                config=self._config,
            )

            self._operation_count += 1
            return resume

        except Exception as exc:
            if isinstance(exc, SessionError):
                raise
            raise SessionError(
                f"Failed to load resume '{name}': {exc}", session_id=self._session_id
            ) from exc

    def generate_all(
        self,
        format: OutputFormat | str = OutputFormat.PDF,
        *,
        pattern: str = "*",
        open_after: bool | None = None,
        parallel: bool = False,
        **kwargs: Any,
    ) -> BatchGenerationResult:
        """Generate all resumes in the session.

        Args:
            format: Output format ("pdf" or "html").
            pattern: Glob pattern for resume names (default: all).
            open_after: Whether to open generated files (overrides session default).
            parallel: Whether to generate in parallel (future enhancement).
            **kwargs: Additional generation options.

        Returns:
            `BatchGenerationResult` with all generation results.

        Raises:
            `SessionError`: If the session is not active.
            `ValueError`: If the format is not supported.

        """
        if not self._is_active:
            raise SessionError(
                "Cannot generate resumes - session is not active",
                session_id=self._session_id,
            )

        try:
            format_enum = OutputFormat.normalize(format)
        except (ValueError, TypeError):
            raise ValueError(
                f"Unsupported format: {format}. Use 'pdf' or 'html'."
            ) from None

        if format_enum not in (OutputFormat.PDF, OutputFormat.HTML):
            raise ValueError(
                f"Unsupported format: {format_enum.value}. Use 'pdf' or 'html'."
            )

        # Use session default for open_after if not specified
        if open_after is None:
            open_after = self._config.auto_open

        start_time = time.time()
        results: dict[str, GenerationResult] = {}
        errors: dict[str, Exception] = {}

        # Find all YAML files in input directory
        yaml_files = self._find_yaml_files(pattern)

        if not yaml_files:
            return BatchGenerationResult(
                results={},
                total_time=time.time() - start_time,
                successful=0,
                failed=0,
                errors={},
            )

        # Generate each resume
        for yaml_file in yaml_files:
            resume_name = yaml_file.stem
            try:
                # Load and generate resume
                resume = self.resume(resume_name, use_cache=True)

                # Apply config overrides (like palette_file) to resume
                if kwargs:
                    resume = resume.with_config(**kwargs)

                if format_enum is OutputFormat.PDF:
                    result = to_pdf(resume, open_after=open_after)
                else:  # html
                    result = to_html(resume, open_after=open_after)

                results[resume_name] = result
                self._generation_times.append(time.time() - start_time)

            except Exception as exc:
                errors[resume_name] = exc
                continue

        total_time = time.time() - start_time
        self._operation_count += len(yaml_files)

        return BatchGenerationResult(
            results=results,
            total_time=total_time,
            successful=len(results),
            failed=len(errors),
            errors=errors,
            formats=[format_enum.value],
        )

    def _find_yaml_files(self, pattern: str = "*") -> list[Path]:
        """Find YAML files matching the given pattern."""
        return find_yaml_files(self._paths.input, pattern)

    def invalidate_cache(self, name: str | None = None) -> None:
        """Invalidate cached resume data.

        Args:
            name: Specific resume name to invalidate, or `None` for all.

        """
        self._repository.invalidate_cache(name)

    def get_cache_info(self) -> dict[str, Any]:
        """Return information about cached resume data.

        Returns:
            Dictionary with cache statistics.

        """
        return {
            "cached_resumes": self._repository.get_cache_keys(),
            "cache_size": self._repository.get_cache_size(),
            "memory_usage_estimate": self._repository.get_memory_usage(),
        }

    def close(self) -> None:
        """Close the session and clean up resources.

        This method is called automatically when using the context manager.
        """
        if self._is_active:
            # Clear cache
            self._repository.clear_cache()
            self._generation_times.clear()
            self._is_active = False

    def __enter__(self) -> ResumeSession:
        """Provide context manager entry."""
        if not self._is_active:
            raise SessionError(
                "Cannot enter inactive session", session_id=self._session_id
            )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Provide context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """Return a detailed string representation."""
        return (
            f"ResumeSession(id={self._session_id[:8]}..., "
            f"active={self._is_active}, operations={self._operation_count})"
        )

    def __str__(self) -> str:
        """Return a string representation of the session."""
        return f"ResumeSession({self._session_id[:8]}...)"


# Convenience function for creating sessions
@contextmanager
def create_session(
    data_dir: str | Path | None = None,
    *,
    paths: Paths | None = None,
    config: SessionConfig | None = None,
    **path_overrides: str | Path,
) -> Generator[ResumeSession, None, None]:
    """Create and manage a `ResumeSession` context.

    This is a convenience function for creating sessions with common defaults.

    Args:
        data_dir: Base data directory.
        paths: Optional pre-resolved `Paths` object.
        config: Optional session configuration.
        **path_overrides: Path configuration overrides.

    Yields:
        `ResumeSession` instance.

    """
    session = ResumeSession(
        data_dir,
        paths=paths,
        config=config,
        **path_overrides,
    )
    try:
        with session as s:
            yield s
    finally:
        session.close()


__all__ = [
    "ResumeSession",
    "SessionConfig",
    "create_session",
]
