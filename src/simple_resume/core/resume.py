"""Provide core resume data transformations as pure functions without side effects.

All functions here are pure data transformations that take inputs and return outputs
without external dependencies or side effects.
"""

from __future__ import annotations

import copy

# subprocess is used to launch viewer tooling with controlled arguments during
# optional preview flows.
import subprocess  # nosec B404
import time
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Any

from weasyprint import CSS, HTML

from ..config import Paths
from ..constants import OutputFormat, RenderMode

# Import new API components
from ..exceptions import (
    ConfigurationError,
    FileSystemError,
    GenerationError,
    TemplateError,
    ValidationError,
)
from ..latex_renderer import (
    LatexCompilationError,
    compile_tex_to_pdf,
    render_resume_latex_from_data,
)
from ..rendering import get_template_environment
from ..result import GenerationMetadata, GenerationResult
from ..utilities import (
    get_content,
    load_palette_from_file,
    normalize_config,
    render_markdown_content,
)
from . import html_generation as _html_generation
from . import pdf_generation as _pdf_generation
from .io_utils import candidate_yaml_path, resolve_paths_for_read
from .models import RenderPlan, ResumeConfig, ValidationResult
from .pdf_generation import LatexGenerationContext
from .plan import (
    prepare_render_data as plan_prepare_render_data,
)
from .plan import (
    validate_resume_config,
    validate_resume_config_or_raise,
)


@contextmanager
def _temporary_backend_bindings(
    module: ModuleType, **overrides: Any
) -> Any:  # pragma: no cover - simple helper
    """Temporarily override module attributes during backend execution."""
    originals: dict[str, Any] = {}
    for name, value in overrides.items():
        originals[name] = getattr(module, name, None)
        setattr(module, name, value)
    try:
        yield
    finally:
        for name, original in originals.items():
            setattr(module, name, original)


class Resume:
    """Manage resume operations with symmetric I/O and method chaining support.

    This class provides an API for resume operations, featuring:
    - Symmetric read/write methods (`read_yaml`/`to_pdf`/`to_html`).
    - Method chaining for fluent interfaces.
    - Rich result objects.
    - Comprehensive error handling.
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

    # Class methods for symmetric I/O patterns (pandas-style).

    @classmethod
    def read_yaml(
        cls,
        name: str = "",
        *,
        paths: Paths | None = None,
        transform_markdown: bool = True,
        **path_overrides: str | Path,
    ) -> Resume:
        """Load a resume from a YAML file.

        Args:
            name: Resume identifier without extension.
            paths: Optional pre-resolved paths.
            transform_markdown: Whether to transform markdown to HTML.
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

            overrides = dict(path_overrides)
            candidate_path = candidate_yaml_path(name)
            resolved_paths = resolve_paths_for_read(paths, overrides, candidate_path)
            raw_data = get_content(name, paths=resolved_paths, transform_markdown=False)

            data = (
                render_markdown_content(raw_data)
                if transform_markdown
                else copy.deepcopy(raw_data)
            )

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

    # Instance methods for output operations (symmetric to read_yaml)

    def to_pdf(
        self,
        output_path: Path | str | None = None,
        *,
        open_after: bool = False,
        **kwargs: Any,
    ) -> GenerationResult:
        """Export to PDF (symmetric to `read_yaml`).

        Args:
            output_path: Optional output path (defaults to output directory).
            open_after: Whether to open the PDF after generation.
            **kwargs: Additional generation options.

        Returns:
            `GenerationResult` with metadata and operations.

        Raises:
            `GenerationError`: If PDF generation fails.
            `ValidationError`: If resume data is invalid.

        """
        start_time = time.time()

        try:
            # Validate data first.
            self.validate_or_raise()

            # Prepare render plan.
            render_plan = self._prepare_render_plan(preview=False)

            # Determine output path.
            if output_path is None:
                if self._paths is None:
                    raise ConfigurationError(
                        "No paths available - provide output_path or create with paths",
                        filename=self._filename,
                    )
                output_path = self._paths.output / f"{self._name}.pdf"
            else:
                output_path = Path(output_path)

            # Generate PDF using backend selected by render mode.
            backend_result = self._generate_pdf(
                render_plan,
                output_path,
                **kwargs,
            )

            # Normalize backend result to consistent format.
            raw_output_path, file_size, page_count = self._normalize_backend_result(
                backend_result
            )

            # Create rich result object.
            generation_time = time.time() - start_time
            template_name = (
                (render_plan.template_name or "latex/basic.tex")
                if render_plan.mode is RenderMode.LATEX
                else (render_plan.template_name or "unknown")
            )

            metadata = GenerationMetadata(
                format_type="pdf",
                template_name=template_name,
                generation_time=generation_time,
                file_size=file_size,
                resume_name=self._name,
                palette_info=render_plan.palette_metadata,
                page_count=page_count,
            )

            generation_result = GenerationResult(raw_output_path, "pdf", metadata)

            if open_after:
                generation_result.open()

            return generation_result

        except Exception as exc:
            if isinstance(exc, (ValidationError, GenerationError, ConfigurationError)):
                raise
            raise GenerationError(
                f"Failed to generate PDF: {exc}",
                format_type="pdf",
                output_path=output_path,
                filename=self._filename,
            ) from exc

    def to_html(
        self,
        output_path: Path | str | None = None,
        *,
        open_after: bool = False,
        browser: str | None = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """Export to HTML (symmetric to `read_yaml`).

        Args:
            output_path: Optional output path (defaults to output directory).
            open_after: Whether to open HTML after generation.
            browser: Optional browser command for opening.
            **kwargs: Additional generation options.

        Returns:
            `GenerationResult` with metadata and operations.

        Raises:
            `GenerationError`: If HTML generation fails.
            `ValidationError`: If resume data is invalid.

        """
        start_time = time.time()

        try:
            # Validate data first.
            self.validate_or_raise()

            # Prepare render plan.
            render_plan = self._prepare_render_plan(preview=True)

            # Determine output path.
            if output_path is None:
                if self._paths is None:
                    raise ConfigurationError(
                        "No paths available - provide output_path or create with paths",
                        filename=self._filename,
                    )
                output_path = self._paths.output / f"{self._name}.html"
            else:
                output_path = Path(output_path)

            # Generate HTML.
            result = self._generate_html(render_plan, output_path, **kwargs)

            # Create rich result object.
            generation_time = time.time() - start_time
            metadata = GenerationMetadata(
                format_type="html",
                template_name=render_plan.template_name or "unknown",
                generation_time=generation_time,
                file_size=result.size,
                resume_name=self._name,
                palette_info=render_plan.palette_metadata,
            )

            generation_result = GenerationResult(output_path, "html", metadata)

            if open_after:
                if browser:
                    # Use specified browser command for opening the file.
                    # Bandit: browser executable originates from user input and
                    # is invoked with a single file.
                    subprocess.Popen(  # noqa: S603  # nosec B603
                        [browser, output_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    generation_result.open()

            return generation_result

        except Exception as exc:
            if isinstance(exc, (ValidationError, GenerationError, ConfigurationError)):
                raise
            raise GenerationError(
                f"Failed to generate HTML: {exc}",
                format_type="html",
                output_path=output_path,
                filename=self._filename,
            ) from exc

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
                palette_payload = load_palette_from_file(palette_file)
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
            new_data["config"], _ = normalize_config(
                new_data["config"], filename=self._filename or ""
            )
            new_raw["config"], _ = normalize_config(
                new_raw["config"], filename=self._filename or ""
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

    # ------------------------------------------------------------------
    # Backend helpers (legacy-compatible for unit tests)
    # ------------------------------------------------------------------

    def _cleanup_latex_artifacts(
        self, tex_path: Path, *, preserve_log: bool = False
    ) -> None:
        """Remove auxiliary files emitted during LaTeX compilation."""
        for suffix in (".aux", ".log", ".out"):
            if preserve_log and suffix == ".log":
                continue
            candidate = tex_path.with_suffix(suffix)
            try:
                if candidate.exists():
                    candidate.unlink()
            except OSError:
                continue

    def _generate_pdf_with_weasyprint(
        self, render_plan: RenderPlan, output_path: Path
    ) -> tuple[GenerationResult, int | None]:
        """Delegate to the HTML-to-PDF backend with patchable dependencies."""
        resume_name = self._name or render_plan.name
        weasy_html = HTML
        weasy_css = CSS
        with _temporary_backend_bindings(
            _pdf_generation,
            get_template_environment=get_template_environment,
            WEASYPRINT_HTML=weasy_html,
            WEASYPRINT_CSS=weasy_css,
        ):
            return _pdf_generation.generate_pdf_with_weasyprint(
                render_plan,
                output_path,
                resume_name=resume_name,
                filename=self._filename,
            )

    def _generate_pdf_with_latex(
        self, render_plan: RenderPlan, output_path: Path
    ) -> tuple[GenerationResult, int | None]:
        """Delegate to the LaTeX backend while exposing legacy hooks."""
        raw_data = self._raw_data if hasattr(self, "_raw_data") else None
        bindings = {
            "render_resume_latex_from_data": render_resume_latex_from_data,
            "compile_tex_to_pdf": compile_tex_to_pdf,
            "LatexCompilationError": LatexCompilationError,
            "cleanup_latex_artifacts": self._cleanup_latex_artifacts,
        }
        with _temporary_backend_bindings(_pdf_generation, **bindings):
            context = LatexGenerationContext(
                raw_data=raw_data,
                processed_data=self._data,
                paths=self._paths,
                filename=self._filename,
            )
            return _pdf_generation.generate_pdf_with_latex(
                render_plan,
                output_path,
                context,
            )

    def _generate_html_with_jinja(
        self, render_plan: RenderPlan, output_path: Path
    ) -> GenerationResult:
        """Render HTML via Jinja with injectable template environment."""
        with _temporary_backend_bindings(
            _html_generation,
            get_template_environment=get_template_environment,
        ):
            return _html_generation.generate_html_with_jinja(
                render_plan,
                output_path,
                filename=self._filename,
            )

    def _normalize_backend_result(
        self,
        generation_output: GenerationResult | tuple[GenerationResult, int | None],
    ) -> tuple[Path, int, int | None]:
        """Normalize backend result to a consistent format.

        Args:
            generation_output: Result from PDF/HTML generation (tuple or
                `GenerationResult`).

        Returns:
            Tuple of (output_path, file_size, page_count).

        """
        # Extract result object and page count
        page_count: int | None
        if isinstance(generation_output, tuple):
            result_object, page_count_candidate = generation_output
            page_count = (
                page_count_candidate
                if isinstance(page_count_candidate, int) and page_count_candidate >= 0
                else None
            )
        else:
            result_object = generation_output
            metadata = getattr(result_object, "metadata", None)
            count_candidate = (
                getattr(metadata, "page_count", None) if metadata else None
            )
            page_count = (
                count_candidate
                if isinstance(count_candidate, int) and count_candidate >= 0
                else None
            )

        # Extract output path
        output_file_path = getattr(result_object, "output_path", None)
        if not isinstance(output_file_path, Path):
            output_file_path = (
                Path(str(output_file_path)) if output_file_path else Path()
            )

        # Extract file size
        reported_size = getattr(result_object, "size", None)
        file_size: int = (
            reported_size
            if isinstance(reported_size, int) and reported_size >= 0
            else 0
        )

        return output_file_path, file_size, page_count

    def generate(
        self,
        format: OutputFormat | str = OutputFormat.PDF,
        output_path: Path | str | None = None,
        *,
        open_after: bool = False,
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate a resume in the specified format.

        Args:
            format: Output format enum (pdf or html).
            output_path: Optional output path.
            open_after: Whether to open after generation.
            **kwargs: Additional generation options.

        Returns:
            `GenerationResult` with metadata and operations.

        Raises:
            `ValueError`: If format is not supported.

        """
        try:
            format_enum = (
                format
                if isinstance(format, OutputFormat)
                else OutputFormat.normalize(format)
            )
        except (ValueError, TypeError):
            raise ValueError(
                f"Unsupported format: {format}. Use 'pdf' or 'html'."
            ) from None

        if format_enum is OutputFormat.PDF:
            return self.to_pdf(output_path, open_after=open_after, **kwargs)

        if format_enum is OutputFormat.HTML:
            return self.to_html(output_path, open_after=open_after, **kwargs)

        raise ValueError(
            f"Unsupported format: {format_enum.value}. Use 'pdf' or 'html'."
        )

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
            self._validation_result = self.validate_config(raw_config, filename)
        return self._validation_result

    def validate_or_raise(self) -> ValidationResult:
        """Validate resume data and raise `ValidationError` on failure.

        This method validates the resume and raises a `ValidationError` if validation
        fails. It's used internally by `to_pdf()`, `to_html()`, and other operations
        requiring valid data.

        Use this for:
        - Fail-fast behavior (stop execution on invalid data).
        - Automatic exception propagation.
        - Validation before an operation requiring valid data.

        For inspection without raising, use `validate()` instead.

        Returns:
            `ValidationResult`: The validation result (only if validation succeeds).

        Raises:
            `ValidationError`: If validation fails with detailed error information.

        Example:
            >>> result = resume.validate_or_raise()  # Raises if invalid, returns result
            >>> resume.to_pdf("output.pdf")  # Only runs if validation passed

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

    def _prepare_render_plan(self, preview: bool | None = None) -> RenderPlan:
        """Prepare a render plan for this resume.

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
            self._render_plan = plan_prepare_render_data(
                source_data,
                preview=actual_preview,
                base_path=base_path,
            )
            self._is_preview = actual_preview

        if self._render_plan is None:  # pragma: no cover - defensive
            raise RuntimeError("Render plan was not prepared")
        return self._render_plan

    def _generate_pdf(
        self, render_plan: RenderPlan, output_path: Path, **kwargs: Any
    ) -> GenerationResult | tuple[GenerationResult, int | None]:
        """Dispatch PDF generation to the appropriate backend."""
        if render_plan.mode is RenderMode.LATEX:
            return self._generate_pdf_with_latex(render_plan, output_path)

        return self._generate_pdf_with_weasyprint(render_plan, output_path)

    def _generate_html(
        self, render_plan: RenderPlan, output_path: Path, **kwargs: Any
    ) -> GenerationResult:
        """Generate HTML using the configured backend."""
        if render_plan.mode is RenderMode.LATEX:
            raise TemplateError(
                "LaTeX mode not supported in HTML generation method",
                template_name="latex",
                filename=self._filename,
            )
        return self._generate_html_with_jinja(render_plan, output_path)

    @staticmethod
    def prepare_render_data(
        source_yaml_content: dict[str, Any],
        *,
        preview: bool = False,
        base_path: Path | str = "",
    ) -> RenderPlan:
        """Transform raw resume data into a render plan.

        Args:
            source_yaml_content: Unprocessed resume data from YAML file.
            preview: Whether this is for preview mode.
            base_path: Base path for resolving assets.

        Returns:
            `RenderPlan` with all necessary information for rendering.

        """
        return plan_prepare_render_data(
            source_yaml_content,
            preview=preview,
            base_path=base_path,
        )

    # ------------------------------------------------------------------
    # Compatibility helpers (public API surface)
    # ------------------------------------------------------------------

    @staticmethod
    def validate_config(
        raw_config: dict[str, Any], filename: str = ""
    ) -> ValidationResult:
        """Validate and normalize resume configuration (compat layer)."""
        return validate_resume_config(raw_config, filename)

    @staticmethod
    def validate_config_or_raise(
        raw_config: dict[str, Any], filename: str = ""
    ) -> ResumeConfig:
        """Validate configuration and raise ``ValidationError`` on failure."""
        return validate_resume_config_or_raise(raw_config, filename)


__all__ = ["Resume", "ResumeConfig", "RenderPlan", "ValidationResult", "RenderMode"]
