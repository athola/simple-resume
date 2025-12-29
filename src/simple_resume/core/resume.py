"""Provide core resume data transformations as pure functions without side effects.

All functions here are pure data transformations that take inputs and return outputs
without external dependencies or side effects.

The core Resume class is a pure data container with:
- Data access and transformation methods
- Validation (pure)
- Method chaining for configuration
- Render plan preparation (pure data transformation)

I/O operations (PDF generation, HTML generation, file opening) are handled by the
shell layer through functions like `to_pdf()` and `to_html()` in the shell module.
"""

from __future__ import annotations

import copy
from functools import lru_cache
from pathlib import Path
from typing import Any

from simple_resume.core.config import normalize_config
from simple_resume.core.exceptions import (
    ConfigurationError,
    FileSystemError,
    ValidationError,
)
from simple_resume.core.models import RenderPlan, ValidationResult
from simple_resume.core.paths import Paths
from simple_resume.core.protocols import (
    ContentLoader,
    PaletteLoader,
    PathResolver,
)
from simple_resume.core.render.plan import (
    prepare_render_data,
    validate_resume_config,
)


# Module-level dependency injection container
class _ResumeDependencyContainer:
    """Container for Resume module dependencies (avoids global statement)."""

    content_loader: ContentLoader | None = None
    palette_loader: PaletteLoader | None = None
    palette_registry_provider: Any | None = None
    path_resolver: PathResolver | None = None


@lru_cache(maxsize=1)
def _get_dependency_container() -> _ResumeDependencyContainer:
    """Return the lazily created dependency container singleton."""
    return _ResumeDependencyContainer()


def set_default_loaders(
    content_loader: ContentLoader | None = None,
    palette_loader: PaletteLoader | None = None,
    path_resolver: PathResolver | None = None,
    palette_registry_provider: Any | None = None,
) -> None:
    """Set default loaders for Resume operations.

    This function is called by the shell layer during initialization
    to inject the default implementations. Core code should not call this.

    Args:
        content_loader: Default content loader implementation.
        palette_loader: Default palette loader implementation.
        path_resolver: Default path resolver implementation.
        palette_registry_provider: Callable returning the palette registry.

    """
    deps = _get_dependency_container()

    if content_loader is not None:
        deps.content_loader = content_loader
    if palette_loader is not None:
        deps.palette_loader = palette_loader
    if path_resolver is not None:
        deps.path_resolver = path_resolver
    if palette_registry_provider is not None:
        deps.palette_registry_provider = palette_registry_provider


def _get_content_loader(injected: ContentLoader | None) -> ContentLoader:
    """Get content loader, preferring injected over default."""
    deps = _get_dependency_container()

    if injected is not None:
        return injected
    if deps.content_loader is not None:
        return deps.content_loader
    raise ConfigurationError(
        "No content loader available. "
        "Either inject one or ensure shell layer is initialized."
    )


def _get_path_resolver(injected: PathResolver | None) -> PathResolver:
    """Get path resolver, preferring injected over default."""
    deps = _get_dependency_container()

    if injected is not None:
        return injected
    if deps.path_resolver is not None:
        return deps.path_resolver
    raise ConfigurationError(
        "No path resolver available. "
        "Either inject one or ensure shell layer is initialized."
    )


def _load_palette_from_file(path: str | Path) -> dict[str, Any]:
    """Load palette from file using the default palette loader."""
    deps = _get_dependency_container()

    if deps.palette_loader is None:
        raise ConfigurationError(
            "No palette loader available. Ensure shell layer is initialized."
        )
    return deps.palette_loader.load_palette_from_file(path)


def _get_palette_registry() -> Any:
    """Resolve palette registry via injected provider to avoid shell import."""
    deps = _get_dependency_container()

    if deps.palette_registry_provider is None:
        raise ConfigurationError(
            "No palette registry provider available. Ensure shell layer is initialized."
        )
    return deps.palette_registry_provider()


class Resume:
    """Core resume data container with pure transformation methods.

    This class provides a pure functional API for resume data:
    - Factory methods for loading (`read_yaml`, `from_data`)
    - Method chaining for configuration (`with_template`, `with_palette`, `with_config`)
    - Validation methods (`validate`, `validate_or_raise`)
    - Render plan preparation (`prepare_render_plan`)

    I/O operations (PDF/HTML generation) are handled by the shell layer.
    Use `simple_resume.to_pdf()` and `simple_resume.to_html()` for generation.
    """

    def __init__(
        self,
        processed_resume_data: dict[str, Any],
        *,
        name: str | None = None,
        paths: Paths | None = None,
        filename: str | None = None,
        source_yaml_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a `Resume` instance.

        Args:
            processed_resume_data: Transformed resume data (markdown rendered,
                normalized).
            name: Optional name identifier.
            paths: Optional resolved paths object.
            filename: Optional source filename for error reporting.
            source_yaml_data: Optional untransformed YAML data before processing.

        """
        self._data = copy.deepcopy(processed_resume_data)
        self._raw_data = (
            copy.deepcopy(source_yaml_data)
            if source_yaml_data is not None
            else copy.deepcopy(processed_resume_data)
        )
        self._name = name or processed_resume_data.get("full_name", "resume")
        self._paths = paths
        self._filename = filename
        self._validation_result: ValidationResult | None = None
        self._render_plan: RenderPlan | None = None
        self._is_preview = False

    @property
    def name(self) -> str:
        """Get the resume name."""
        return self._name

    @property
    def data(self) -> dict[str, Any]:
        """Get the processed resume data (read-only copy)."""
        return copy.deepcopy(self._data)

    @property
    def raw_data(self) -> dict[str, Any]:
        """Get the raw resume data before processing (read-only copy)."""
        return copy.deepcopy(self._raw_data)

    @property
    def paths(self) -> Paths | None:
        """Get the resolved paths for this resume."""
        return self._paths

    @property
    def filename(self) -> str | None:
        """Get the source filename for error reporting."""
        return self._filename

    # Class methods for symmetric I/O patterns (pandas-style).

    @classmethod
    def read_yaml(
        cls,
        name: str = "",
        *,
        paths: Paths | None = None,
        transform_markdown: bool = True,
        content_loader: ContentLoader | None = None,
        path_resolver: PathResolver | None = None,
        **path_overrides: str | Path,
    ) -> Resume:
        """Load a resume from a YAML file.

        Args:
            name: Resume identifier without extension.
            paths: Optional pre-resolved paths.
            transform_markdown: Whether to transform markdown to HTML.
            content_loader: Optional custom content loader (for dependency injection).
            path_resolver: Optional custom path resolver (for dependency injection).
            **path_overrides: Path configuration overrides.

        Returns:
            `Resume` instance loaded from YAML file.

        Raises:
            `FileSystemError`: If file cannot be read.
            `ValidationError`: If resume data is invalid.

        """
        try:
            if path_overrides and paths is not None:
                raise ConfigurationError(
                    "Provide either paths or path_overrides, not both", filename=name
                )

            # Use injected dependencies or get defaults
            loader = _get_content_loader(content_loader)
            resolver = _get_path_resolver(path_resolver)

            # Resolve paths for determining filename
            overrides = dict(path_overrides)
            candidate_path = resolver.candidate_yaml_path(name)
            resolved_paths = resolver.resolve_paths_for_read(
                paths, overrides, candidate_path
            )

            # Load content
            data, raw_data = loader.load(name, resolved_paths, transform_markdown)

            resume_identifier = (
                candidate_path.stem if candidate_path is not None else str(name)
            )
            filename_label = (
                str(candidate_path) if candidate_path is not None else str(name)
            )

            return cls(
                processed_resume_data=data,
                name=resume_identifier,
                paths=resolved_paths,
                filename=filename_label,
                source_yaml_data=raw_data,
            )

        except Exception as exc:
            if isinstance(exc, (ValidationError, ConfigurationError)):
                raise
            raise FileSystemError(
                f"Failed to read resume YAML '{name}': {exc}",
                path=name,
                operation="read",
            ) from exc

    @classmethod
    def from_data(
        cls,
        data: dict[str, Any],
        *,
        name: str | None = None,
        paths: Paths | None = None,
        raw_data: dict[str, Any] | None = None,
    ) -> Resume:
        """Create a `Resume` from dictionary data.

        Args:
            data: Resume data dictionary.
            name: Optional name identifier.
            paths: Optional resolved paths object.
            raw_data: Optional untransformed resume data.

        Returns:
            `Resume` instance created from data.

        """
        return cls(
            processed_resume_data=data,
            name=name,
            paths=paths,
            source_yaml_data=raw_data,
        )

    # Method chaining support (fluent interface)

    def with_template(self, template_name: str) -> Resume:
        """Return a new `Resume` with a different template.

        Args:
            template_name: Name of template to use.

        Returns:
            New `Resume` instance with updated template.

        """
        new_data = copy.deepcopy(self._data)
        new_raw = (
            copy.deepcopy(self._raw_data)
            if getattr(self, "_raw_data", None) is not None
            else copy.deepcopy(self._data)
        )

        # Template is stored at root level, not in config (see line 908)
        new_data["template"] = template_name  # pytype: disable=container-type-mismatch
        new_raw["template"] = template_name  # pytype: disable=container-type-mismatch

        return Resume(
            processed_resume_data=new_data,
            name=self._name,
            paths=self._paths,
            filename=self._filename,
            source_yaml_data=new_raw,
        )

    def with_theme(self, theme_name: str) -> Resume:
        """Return a new `Resume` with a theme applied.

        Themes provide preset configurations (colors, layout, spacing).
        User configuration overrides theme defaults.

        Available themes: modern, classic, bold, minimal, executive

        Args:
            theme_name: Name of the theme to apply.

        Returns:
            New `Resume` instance with theme configuration applied.

        Example:
            >>> resume = Resume.read_yaml("my_resume").with_theme("modern")

        """
        new_data = copy.deepcopy(self._data)
        new_raw = (
            copy.deepcopy(self._raw_data)
            if getattr(self, "_raw_data", None) is not None
            else copy.deepcopy(self._data)
        )

        # Add theme key - will be resolved by shell layer during processing
        new_raw["theme"] = theme_name

        return Resume(
            processed_resume_data=new_data,
            name=self._name,
            paths=self._paths,
            filename=self._filename,
            source_yaml_data=new_raw,
        )

    def with_palette(self, palette: str | dict[str, Any]) -> Resume:
        """Return a new `Resume` with a different color palette.

        Args:
            palette: Either palette name (`str`) or palette configuration `dict`.

        Returns:
            New `Resume` instance with updated palette.

        """
        new_data = copy.deepcopy(self._data)
        new_raw = (
            copy.deepcopy(self._raw_data)
            if getattr(self, "_raw_data", None) is not None
            else copy.deepcopy(self._data)
        )

        if isinstance(palette, str):
            # Apply palette by name
            if "config" not in new_data:
                new_data["config"] = {}
            if "config" not in new_raw:
                new_raw["config"] = {}
            new_data["config"]["color_scheme"] = palette
            new_raw["config"]["color_scheme"] = palette
        else:
            # Apply palette configuration
            if "config" not in new_data:
                new_data["config"] = {}
            if "config" not in new_raw:
                new_raw["config"] = {}
            new_data["config"]["palette"] = palette
            new_raw["config"]["palette"] = palette

        return Resume(
            processed_resume_data=new_data,
            name=self._name,
            paths=self._paths,
            filename=self._filename,
            source_yaml_data=new_raw,
        )

    def with_config(self, **config_overrides: Any) -> Resume:
        """Return a new `Resume` with configuration changes.

        Args:
            **config_overrides: Configuration key-value pairs to override.

        Returns:
            New `Resume` instance with updated configuration.

        """
        new_data = copy.deepcopy(self._data)
        new_raw = (
            copy.deepcopy(self._raw_data)
            if getattr(self, "_raw_data", None) is not None
            else copy.deepcopy(self._data)
        )
        if "config" not in new_data:
            new_data["config"] = {}
        if "config" not in new_raw:
            new_raw["config"] = {}

        overrides = dict(config_overrides)
        palette_file = overrides.pop("palette_file", None)

        if palette_file is not None:
            try:
                palette_payload = _load_palette_from_file(palette_file)
            except (FileNotFoundError, ValueError) as exc:
                raise ConfigurationError(
                    f"Failed to load palette file: {palette_file}",
                    filename=self._filename,
                ) from exc

            palette_data = copy.deepcopy(palette_payload["palette"])
            new_data["config"]["palette"] = copy.deepcopy(palette_data)
            new_raw["config"]["palette"] = copy.deepcopy(palette_data)

            # Apply the palette block to individual color fields
            # Normalize both data structures to apply palette colors
            registry = _get_palette_registry()
            new_data["config"], _ = normalize_config(
                new_data["config"], filename=self._filename or "", registry=registry
            )
            new_raw["config"], _ = normalize_config(
                new_raw["config"], filename=self._filename or "", registry=registry
            )

        palette_override = overrides.get("palette")
        if isinstance(palette_override, dict):
            overrides["palette"] = copy.deepcopy(palette_override)

        new_data["config"].update(overrides)
        new_raw["config"].update(overrides)

        return Resume(
            processed_resume_data=new_data,
            name=self._name,
            paths=self._paths,
            filename=self._filename,
            source_yaml_data=new_raw,
        )

    def preview(self) -> Resume:
        """Return `Resume` in preview mode.

        Returns:
            New `Resume` instance configured for preview rendering.

        """
        new_resume = Resume(
            processed_resume_data=self._data,
            name=self._name,
            paths=self._paths,
            filename=self._filename,
            source_yaml_data=self._raw_data,
        )
        new_resume._is_preview = True
        return new_resume

    # Instance methods for validation and rendering

    def validate(self) -> ValidationResult:
        """Validate this resume's data (inspection tier - never raises).

        This method returns a `ValidationResult` object containing validation
        status, errors, and warnings. It never raises exceptions, allowing
        inspection of validation issues without interrupting execution.

        Use this to:
        - Check validation status without stopping execution.
        - Log warnings or collect error information.
        - Build custom error handling logic.

        For fail-fast validation, use `validate_or_raise()` instead.

        Returns:
            `ValidationResult` with validation status and any errors/warnings.

        Example:
            >>> result = resume.validate()
            >>> if not result.is_valid:
            >>>     print(f"Errors: {result.errors}")
            >>> if result.warnings:
            >>>     log.warning(f"Warnings: {result.warnings}")

        """
        if self._validation_result is None:
            raw_config = self._data.get("config", {})
            filename = self._filename or ""
            registry = _get_palette_registry()
            self._validation_result = validate_resume_config(
                raw_config, filename, registry=registry
            )
        return self._validation_result

    def validate_or_raise(self) -> ValidationResult:
        """Validate resume data and raise `ValidationError` on failure.

        This method validates the resume and raises a `ValidationError` if validation
        fails. Use before operations requiring valid data.

        Use this for:
        - Fail-fast behavior (stop execution on invalid data).
        - Automatic exception propagation.
        - Validation before generation operations.

        For inspection without raising, use `validate()` instead.

        Returns:
            `ValidationResult`: The validation result (only if validation succeeds).

        Raises:
            `ValidationError`: If validation fails with detailed error information.

        Example:
            >>> result = resume.validate_or_raise()  # Raises if invalid
            >>> to_pdf(resume, "output.pdf")  # Only runs if validation passed

        """
        validation_result = self.validate()
        if not validation_result.is_valid:
            raise ValidationError(
                f"Resume validation failed: {validation_result.errors}",
                errors=validation_result.errors,
                warnings=validation_result.warnings,
                filename=self._filename,
            )
        return validation_result

    def prepare_render_plan(self, preview: bool | None = None) -> RenderPlan:
        """Prepare a render plan for this resume.

        This method prepares the data needed for rendering the resume in
        various formats. It's called by shell layer generation functions.

        Args:
            preview: Whether to prepare for preview rendering (defaults to setting).

        Returns:
            `RenderPlan` with all necessary rendering information.

        """
        needs_refresh = self._render_plan is None or (
            preview is not None and preview != self._is_preview
        )

        if needs_refresh:
            actual_preview = self._is_preview if preview is None else preview
            base_path: Path | str = self._paths.content if self._paths else Path()
            source_data = (
                self._raw_data
                if hasattr(self, "_raw_data") and self._raw_data is not None
                else self._data
            )
            registry = _get_palette_registry()
            self._render_plan = prepare_render_data(
                source_data,
                preview=actual_preview,
                base_path=base_path,
                registry=registry,
            )
            self._is_preview = actual_preview

        if self._render_plan is None:  # pragma: no cover - defensive
            raise RuntimeError("Render plan was not prepared")
        return self._render_plan


__all__ = ["Resume", "set_default_loaders"]
