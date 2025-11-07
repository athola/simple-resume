"""Core resume data transformations - pure functions without side effects.

This module contains the functional core of the resume system - all functions
here are pure data transformations that take inputs and return outputs without
external dependencies or side effects.
"""

from __future__ import annotations

import copy
import os

# subprocess is used to launch viewer tooling with controlled arguments during
# optional preview flows.
import subprocess  # nosec B404
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol, cast

from ..config import TEMPLATE_LOC, Paths, resolve_paths

# Import new API components
from ..exceptions import (
    ConfigurationError,
    FileSystemError,
    GenerationError,
    TemplateError,
    ValidationError,
)
from ..palettes.exceptions import PaletteGenerationError
from ..rendering import get_template_environment
from ..result import GenerationMetadata, GenerationResult
from ..utilities import (
    _calculate_luminance,
    _get_contrasting_text_color,
    _hex_to_rgb,
    _is_valid_color,
    get_content,
    load_palette_from_file,
    normalize_config,
    render_markdown_content,
)

# Optional imports for PDF generation
try:
    from weasyprint import CSS as WEASYPRINT_CSS
    from weasyprint import HTML as WEASYPRINT_HTML
except ImportError:
    WEASYPRINT_CSS = cast(Any, None)
    WEASYPRINT_HTML = cast(Any, None)

CSS = WEASYPRINT_CSS
HTML = WEASYPRINT_HTML


# Protocol definitions for optional LaTeX imports
class LatexCompilationErrorProtocol(Protocol):
    """Protocol for LaTeX compilation error when LaTeX renderer is not available."""

    log: str | None
    args: tuple[object, ...]


class CompileTexToPdfProtocol(Protocol):
    """Protocol for LaTeX compilation function when LaTeX renderer is not available."""

    def __call__(self, tex_path: Path) -> Path: ...


class RenderResumeLatexProtocol(Protocol):
    """Protocol for LaTeX rendering function when LaTeX renderer is not available."""

    def __call__(self, data: dict[str, Any], *, paths: Any) -> Any: ...


# Optional imports for LaTeX generation (deferred to avoid cycles)
LatexCompilationError: type[LatexCompilationErrorProtocol] | None = None
compile_tex_to_pdf: CompileTexToPdfProtocol | None = None
render_resume_latex_from_data: RenderResumeLatexProtocol | None = None

try:
    from ..latex_renderer import (
        LatexCompilationError,
        compile_tex_to_pdf,
        render_resume_latex_from_data,
    )
except ImportError:
    pass


RenderMode = Literal["html", "latex"]


def _candidate_yaml_path(name: str | os.PathLike[str]) -> Path | None:
    if isinstance(name, (str, os.PathLike)):
        maybe_path = Path(name)
        if maybe_path.suffix.lower() in {".yaml", ".yml"}:
            return maybe_path
    return None


def _resolve_paths_for_read(
    supplied_paths: Paths | None,
    overrides: dict[str, Any],
    candidate: Path | None,
) -> Paths:
    if supplied_paths is not None:
        return supplied_paths

    if overrides:
        return resolve_paths(**overrides)

    if candidate is not None:
        if candidate.parent.name == "input":
            base_dir = candidate.parent.parent
        else:
            base_dir = candidate.parent

        # resolve_paths accepts PathLike (includes Path objects)
        base_paths = resolve_paths(data_dir=base_dir)
        return Paths(
            data=base_paths.data,
            input=candidate.parent,
            output=base_paths.output,
            content=base_paths.content,
            templates=base_paths.templates,
            static=base_paths.static,
        )

    return resolve_paths(**overrides)


@dataclass(frozen=True)
class ResumeConfig:
    """Normalized resume configuration with validated fields."""

    page_width: int | None = None
    page_height: int | None = None
    sidebar_width: int | None = None
    output_mode: str = "markdown"
    template: str = "resume_no_bars"
    color_scheme: str = "default"

    # Color fields
    theme_color: str = "#0395DE"
    sidebar_color: str = "#F6F6F6"
    sidebar_text_color: str = "#000000"
    bar_background_color: str = "#DFDFDF"
    date2_color: str = "#616161"
    frame_color: str = "#757575"
    heading_icon_color: str = "#0395DE"  # Defaults to theme_color


@dataclass(frozen=True)
class RenderPlan:
    """Pure data structure describing how to render a resume."""

    name: str
    mode: RenderMode
    config: ResumeConfig
    template_name: str | None = None
    context: dict[str, Any] | None = None
    tex: str | None = None
    palette_metadata: dict[str, Any] | None = None
    base_path: Path | str = ""  # Accepts Path or str for flexibility


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating resume data."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    normalized_config: ResumeConfig | None = None
    palette_metadata: dict[str, Any] | None = None


class Resume:
    """Enhanced Resume class with symmetric I/O and method chaining support.

    This class provides a pandas-like API for resume operations with:
    - Symmetric read/write methods (read_yaml/to_pdf/to_html)
    - Method chaining for fluent interfaces
    - Rich result objects
    - Comprehensive error handling
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
        """Initialize a Resume instance.

        Args:
            processed_resume_data: Transformed resume data (markdown rendered,
                normalized)
            name: Optional name identifier
            paths: Optional resolved paths object
            filename: Optional source filename for error reporting
            source_yaml_data: Optional untransformed YAML data before processing

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

    # Class methods for symmetric I/O patterns (pandas-style)

    @classmethod
    def read_yaml(
        cls,
        name: str = "",
        *,
        paths: Paths | None = None,
        transform_markdown: bool = True,
        **path_overrides: str | Path,
    ) -> Resume:
        """Load resume from YAML file - pandas-style pattern.

        Args:
            name: Resume identifier without extension
            paths: Optional pre-resolved paths
            transform_markdown: Whether to transform markdown to HTML
            **path_overrides: Path configuration overrides

        Returns:
            Resume instance loaded from YAML file

        Raises:
            FileSystemError: If file cannot be read
            ValidationError: If resume data is invalid

        """
        try:
            if path_overrides and paths is not None:
                raise ConfigurationError(
                    "Provide either paths or path_overrides, not both", filename=name
                )

            overrides = dict(path_overrides)
            candidate_path = _candidate_yaml_path(name)
            resolved_paths = _resolve_paths_for_read(paths, overrides, candidate_path)
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
        """Create Resume from dictionary data.

        Args:
            data: Resume data dictionary
            name: Optional name identifier
            paths: Optional resolved paths object
            raw_data: Optional untransformed resume data

        Returns:
            Resume instance created from data

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
        """Export to PDF - symmetric to read_yaml.

        Args:
            output_path: Optional output path (defaults to output directory)
            open_after: Whether to open the PDF after generation
            **kwargs: Additional generation options

        Returns:
            GenerationResult with metadata and operations

        Raises:
            GenerationError: If PDF generation fails
            ValidationError: If resume data is invalid

        """
        start_time = time.time()

        try:
            # Validate data first
            self.validate_or_raise()

            # Prepare render plan
            render_plan = self._prepare_render_plan(preview=False)

            # Determine output path
            if output_path is None:
                if self._paths is None:
                    raise ConfigurationError(
                        "No paths available - provide output_path or create with paths",
                        filename=self._filename,
                    )
                output_path = self._paths.output / f"{self._name}.pdf"
            else:
                output_path = Path(output_path)

            # Generate PDF using backend selected by render mode
            backend_result = self._generate_pdf(
                render_plan,
                output_path,
                **kwargs,
            )

            # Normalize backend result to consistent format
            raw_output_path, file_size, page_count = self._normalize_backend_result(
                backend_result
            )

            # Create rich result object
            generation_time = time.time() - start_time
            template_name = (
                (render_plan.template_name or "latex/basic.tex")
                if render_plan.mode == "latex"
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
        """Export to HTML - symmetric to read_yaml.

        Args:
            output_path: Optional output path (defaults to output directory)
            open_after: Whether to open HTML after generation
            browser: Optional browser command for opening
            **kwargs: Additional generation options

        Returns:
            GenerationResult with metadata and operations

        Raises:
            GenerationError: If HTML generation fails
            ValidationError: If resume data is invalid

        """
        start_time = time.time()

        try:
            # Validate data first
            self.validate_or_raise()

            # Prepare render plan
            render_plan = self._prepare_render_plan(preview=True)

            # Determine output path
            if output_path is None:
                if self._paths is None:
                    raise ConfigurationError(
                        "No paths available - provide output_path or create with paths",
                        filename=self._filename,
                    )
                output_path = self._paths.output / f"{self._name}.html"
            else:
                output_path = Path(output_path)

            # Generate HTML
            result = self._generate_html(render_plan, output_path, **kwargs)

            # Create rich result object
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
        """Return new Resume with different template.

        Args:
            template_name: Name of template to use

        Returns:
            New Resume instance with updated template

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
        """Return new Resume with different color palette.

        Args:
            palette: Either palette name (str) or palette configuration dict

        Returns:
            New Resume instance with updated palette

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
        """Return new Resume with configuration changes.

        Args:
            **config_overrides: Configuration key-value pairs to override

        Returns:
            New Resume instance with updated configuration

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
            new_data["config"]["palette"] = palette_data
            new_raw["config"]["palette"] = copy.deepcopy(palette_data)

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
        """Return Resume in preview mode.

        Returns:
            New Resume instance configured for preview rendering

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

    def _normalize_backend_result(
        self,
        generation_output: GenerationResult | tuple[GenerationResult, int | None],
    ) -> tuple[Path, int, int | None]:
        """Normalize backend result to consistent format.

        Args:
            generation_output: Result from PDF/HTML generation (tuple or
                GenerationResult)

        Returns:
            Tuple of (output_path, file_size, page_count)

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
        format: str = "pdf",
        output_path: Path | str | None = None,
        *,
        open_after: bool = False,
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate resume in specified format.

        Args:
            format: Output format ("pdf" or "html")
            output_path: Optional output path
            open_after: Whether to open after generation
            **kwargs: Additional generation options

        Returns:
            GenerationResult with metadata and operations

        Raises:
            ValueError: If format is not supported

        """
        format = format.lower()
        if format == "pdf":
            return self.to_pdf(output_path, open_after=open_after, **kwargs)
        elif format == "html":
            return self.to_html(output_path, open_after=open_after, **kwargs)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'pdf' or 'html'.")

    # Instance methods for validation and rendering

    def validate(self) -> ValidationResult:
        """Validate this resume's data (inspection tier - never raises).

        This method returns a ValidationResult object that contains validation
        status, errors, and warnings. It never raises exceptions, allowing you
        to inspect validation issues without interrupting execution.

        Use this when you want to:
        - Check validation status without stopping execution
        - Log warnings or collect error information
        - Build custom error handling logic

        For fail-fast validation, use `validate_or_raise()` instead.

        Returns:
            ValidationResult with validation status and any errors/warnings

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

    def validate_or_raise(self) -> None:
        """Validate resume data and raise ValidationError on failure.

        This method validates the resume and raises a ValidationError if validation
        fails. It's used internally by to_pdf(), to_html(), and other operations
        that require valid data.

        Use this when you want:
        - Fail-fast behavior (stop execution on invalid data)
        - Automatic exception propagation
        - To validate before an operation that requires valid data

        For inspection without raising, use `validate()` instead.

        Raises:
            ValidationError: If validation fails with detailed error information

        Example:
            >>> resume.validate_or_raise()  # Raises if invalid
            >>> resume.to_pdf("output.pdf")  # Only runs if validation passed

        """
        validation_result = self.validate()
        if not validation_result.is_valid:
            raise ValidationError(
                f"Resume validation failed: {validation_result.errors}",
                errors=validation_result.errors,
                filename=self._filename,
            )

    def _prepare_render_plan(self, preview: bool | None = None) -> RenderPlan:
        """Prepare render plan for this resume.

        Args:
            preview: Whether to prepare for preview rendering (defaults to setting)

        Returns:
            RenderPlan with all necessary rendering information

        """
        if self._render_plan is None or (
            preview is not None and preview != self._is_preview
        ):
            actual_preview = preview if preview is not None else self._is_preview
            # Pass Path directly - no need to convert to string
            base_path = self._paths.content if self._paths else Path()
            source_data = (
                self._raw_data
                if hasattr(self, "_raw_data") and self._raw_data is not None
                else self._data
            )
            self._render_plan = self.prepare_render_data(
                source_data, preview=actual_preview, base_path=base_path
            )
        return self._render_plan

    def _generate_pdf(
        self, render_plan: RenderPlan, output_path: Path, **kwargs: Any
    ) -> GenerationResult | tuple[GenerationResult, int | None]:
        """Dispatch PDF generation to the appropriate backend."""
        if render_plan.mode == "latex":
            return self._generate_pdf_with_latex(render_plan, output_path, **kwargs)
        return self._generate_pdf_with_weasyprint(render_plan, output_path, **kwargs)

    def _generate_pdf_with_weasyprint(
        self, render_plan: RenderPlan, output_path: Path, **kwargs: Any
    ) -> tuple[GenerationResult, int | None]:
        """Generate PDF using WeasyPrint backend.

        Args:
            render_plan: Render plan with template and context
            output_path: Output file path
            **kwargs: Additional generation options

        Returns:
            Tuple of (GenerationResult for the generated PDF, page count)

        """
        if CSS is None or HTML is None:
            raise TemplateError(
                "WeasyPrint is required for PDF generation. "
                "Install with: pip install weasyprint",
                template_name=render_plan.template_name,
            )

        if render_plan.mode == "latex":
            raise TemplateError(
                "LaTeX mode not supported in PDF generation method",
                template_name="latex",
                filename=self._filename,
            )

        if not render_plan.context or not render_plan.template_name:
            raise TemplateError(
                "HTML plan missing context or template_name", filename=self._filename
            )

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Render HTML template - use templates directory for template loading
        env = get_template_environment(str(TEMPLATE_LOC))
        html = (
            env.get_template(render_plan.template_name)
            .render(**render_plan.context)
            .lstrip()
        )

        # Determine page dimensions (default to A4: 210mm × 297mm)
        page_width = render_plan.config.page_width or 210
        page_height = render_plan.config.page_height or 297

        # Generate PDF with WeasyPrint
        css = CSS(
            string=f"@page {{size: {page_width}mm {page_height}mm; margin: 0mm;}}"
        )
        html_doc = HTML(string=html, base_url=render_plan.base_path)

        # Render document and determine page count when possible
        document = html_doc.render(stylesheets=[css])
        raw_page_count: int | None = None
        pages = getattr(document, "pages", None)
        if pages is not None:
            try:
                raw_page_count = len(pages)
            except TypeError:
                length_func = getattr(pages, "__len__", None)
                if callable(length_func):
                    try:
                        candidate = length_func()
                        if isinstance(candidate, (int, str, float, bool)):
                            raw_page_count = int(candidate)
                        else:
                            raw_page_count = None
                    except Exception:
                        raw_page_count = None

        page_count = (
            raw_page_count
            if isinstance(raw_page_count, int) and raw_page_count >= 0
            else None
        )

        # Write PDF to file
        html_doc.write_pdf(
            str(output_path),
            stylesheets=[css],
        )

        # Create result (metadata is refined by caller)
        metadata = GenerationMetadata(
            format_type="pdf",
            template_name=render_plan.template_name or "unknown",
            generation_time=0.0,
            file_size=0,
            resume_name=self._name or render_plan.name,
            palette_info=render_plan.palette_metadata,
            page_count=page_count,
        )

        return GenerationResult(output_path, "pdf", metadata), page_count

    def _generate_pdf_with_latex(
        self, render_plan: RenderPlan, output_path: Path, **kwargs: Any
    ) -> tuple[GenerationResult, int | None]:
        """Generate PDF using the LaTeX backend."""
        if self._paths is None:
            raise ConfigurationError(
                "LaTeX generation requires resolved paths", filename=self._filename
            )

        if (
            LatexCompilationError is None
            or compile_tex_to_pdf is None
            or render_resume_latex_from_data is None
        ):
            raise ConfigurationError(
                "LaTeX renderer is required for LaTeX generation. "
                "Install with: pip install simple-resume[latex]",
                filename=self._filename,
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        tex_path = output_path.with_suffix(".tex")
        preserve_log = False
        try:
            latex_source = (
                self._raw_data
                if hasattr(self, "_raw_data") and self._raw_data is not None
                else self._data
            )
            latex_result = render_resume_latex_from_data(
                latex_source,
                paths=self._paths,
            )
            tex_path.write_text(latex_result.tex, encoding="utf-8")
            pdf_path = compile_tex_to_pdf(tex_path)
            if pdf_path != output_path:
                pdf_path.replace(output_path)
        except Exception as exc:
            if LatexCompilationError is not None and isinstance(
                exc, LatexCompilationError
            ):
                if hasattr(exc, "log") and exc.log:
                    tex_path.with_suffix(".log").write_text(exc.log, encoding="utf-8")
                    preserve_log = True
                raise GenerationError(
                    f"LaTeX compilation failed: {exc}",
                    format_type="pdf",
                    output_path=str(output_path),
                    filename=self._filename,
                ) from exc
            else:
                raise
        finally:
            self._cleanup_latex_artifacts(tex_path, preserve_log=preserve_log)

        return GenerationResult(output_path, "pdf"), None

    def _cleanup_latex_artifacts(
        self, tex_path: Path, *, preserve_log: bool = False
    ) -> None:
        """Remove auxiliary files emitted by LaTeX engines."""
        for suffix in (".aux", ".log", ".out"):
            if preserve_log and suffix == ".log":
                continue
            candidate = tex_path.with_suffix(suffix)
            try:
                if candidate.exists():
                    candidate.unlink()
            except OSError:
                continue

    def _generate_html(
        self, render_plan: RenderPlan, output_path: Path, **kwargs: Any
    ) -> GenerationResult:
        """Generate HTML using the configured backend."""
        if render_plan.mode == "latex":
            raise TemplateError(
                "LaTeX mode not supported in HTML generation method",
                template_name="latex",
                filename=self._filename,
            )
        return self._generate_html_with_jinja(render_plan, output_path, **kwargs)

    def _generate_html_with_jinja(
        self, render_plan: RenderPlan, output_path: Path, **kwargs: Any
    ) -> GenerationResult:
        """Generate HTML using Jinja2 template.

        Args:
            render_plan: Render plan with template and context
            output_path: Output file path
            **kwargs: Additional generation options

        Returns:
            GenerationResult for the generated HTML

        """
        if render_plan.mode == "latex":
            raise TemplateError(
                "LaTeX mode not supported in HTML generation method",
                template_name="latex",
                filename=self._filename,
            )

        if not render_plan.context or not render_plan.template_name:
            raise TemplateError(
                "HTML plan missing context or template_name", filename=self._filename
            )

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Render HTML template - use templates directory for template loading
        env = get_template_environment(str(TEMPLATE_LOC))
        html = (
            env.get_template(render_plan.template_name)
            .render(**render_plan.context)
            .lstrip()
        )

        # Add base href for proper asset resolution
        # Normalize to Path if it's a string
        base_path = (
            render_plan.base_path
            if isinstance(render_plan.base_path, Path)
            else Path(render_plan.base_path)
        )
        base_uri = base_path.resolve().as_uri().rstrip("/") + "/"
        base_tag = f'<base href="{base_uri}">'
        if "<head>" in html:
            html_with_base = html.replace("<head>", f"<head>\n  {base_tag}", 1)
        else:
            html_with_base = f"{base_tag}\n{html}"

        # Write HTML file
        output_path.write_text(html_with_base, encoding="utf-8")

        return GenerationResult(output_path, "html")

    # Existing static methods (preserved for compatibility)

    @staticmethod
    def validate_config(
        raw_config: dict[str, Any], filename: str = ""
    ) -> ValidationResult:
        """Validate and normalize resume configuration.

        Args:
            raw_config: Raw configuration dictionary from YAML
            filename: Optional filename for error reporting

        Returns:
            ValidationResult with normalized config and any errors/warnings

        """
        errors: list[str] = []
        warnings: list[str] = []

        try:
            working_config = copy.deepcopy(raw_config)

            color_fields = [
                "theme_color",
                "sidebar_color",
                "sidebar_text_color",
                "bar_background_color",
                "date2_color",
                "frame_color",
                "heading_icon_color",
            ]
            for field in color_fields:
                if field not in working_config:
                    continue
                candidate = working_config.get(field)
                candidate_str = str(candidate) if candidate is not None else ""
                if not _is_valid_color(candidate_str):
                    errors.append(
                        f"Invalid color format for '{field}': {candidate}. "
                        "Expected hex color like '#0395DE' or '#FFF'"
                    )
                    working_config.pop(field, None)

            normalized_config, palette_meta = normalize_config(
                working_config, filename=filename
            )

            # Convert to our pure ResumeConfig
            config = ResumeConfig(
                page_width=normalized_config.get("page_width"),
                page_height=normalized_config.get("page_height"),
                sidebar_width=normalized_config.get("sidebar_width"),
                output_mode=str(normalized_config.get("output_mode", "markdown"))
                .strip()
                .lower(),
                template=normalized_config.get("template", "resume_no_bars"),
                color_scheme=normalized_config.get("color_scheme", "default"),
                theme_color=normalized_config.get("theme_color", "#0395DE"),
                sidebar_color=normalized_config.get("sidebar_color", "#F6F6F6"),
                sidebar_text_color=normalized_config.get(
                    "sidebar_text_color", "#000000"
                ),
                bar_background_color=normalized_config.get(
                    "bar_background_color", "#DFDFDF"
                ),
                date2_color=normalized_config.get("date2_color", "#616161"),
                frame_color=normalized_config.get("frame_color", "#757575"),
                heading_icon_color=normalized_config.get(
                    "heading_icon_color", "#0395DE"
                ),
            )

            if errors:
                return ValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    normalized_config=None,
                    palette_metadata=None,
                )

            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=warnings,
                normalized_config=config,
                palette_metadata=palette_meta,
            )

        except ValueError as exc:
            errors.append(str(exc))
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        except Exception as exc:
            errors.append(f"Unexpected validation error: {exc}")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    @staticmethod
    def validate_config_or_raise(
        raw_config: dict[str, Any], filename: str = ""
    ) -> ResumeConfig:
        """Validate and normalize resume configuration.

        Raises ValidationError when normalization fails.

        Args:
            raw_config: Raw configuration dictionary from YAML
            filename: Optional filename for error reporting

        Returns:
            Normalized ResumeConfig if validation succeeds

        Raises:
            ValidationError: If validation fails with detailed error information

        """
        result = Resume.validate_config(raw_config, filename)
        if not result.is_valid:
            raise ValidationError(
                f"Configuration validation failed: {result.errors}",
                errors=result.errors,
                filename=filename,
            )

        if result.normalized_config is None:
            raise ValidationError(
                "Configuration validation failed: No normalized config produced",
                errors=["Internal validation error"],
                filename=filename,
            )

        return result.normalized_config

    @staticmethod
    def _normalize_with_palette_fallback(
        raw_config: dict[str, Any],
        *,
        palette_meta_source: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], Any, dict[str, Any]]:
        """Normalize a raw config while handling palette generation failures."""
        config_for_validation = raw_config

        try:
            normalized_config_dict, palette_meta = normalize_config(raw_config)
            return normalized_config_dict, palette_meta, config_for_validation
        except PaletteGenerationError:
            fallback_meta = None
            if isinstance(palette_meta_source, dict):
                fallback_meta = palette_meta_source.get("palette")

            cleaned_config = copy.deepcopy(raw_config)
            cleaned_config.pop("palette", None)
            normalized_config_dict, _ = normalize_config(cleaned_config)

            return normalized_config_dict, fallback_meta, cleaned_config

    @staticmethod
    def _validate_normalized_config(config_data: dict[str, Any]) -> ResumeConfig:
        """Validate normalized configuration data."""
        return Resume.validate_config_or_raise(config_data)

    @staticmethod
    def _transform_for_mode(
        source_yaml_content: dict[str, Any], mode: RenderMode
    ) -> dict[str, Any]:
        """Transform YAML content based on render mode."""
        if mode == "latex":
            return copy.deepcopy(source_yaml_content)

        return render_markdown_content(source_yaml_content)

    @staticmethod
    def _build_render_plan(  # noqa: PLR0913
        name: str,
        mode: RenderMode,
        config: ResumeConfig,
        context: dict[str, Any] | None,
        *,
        base_path: Path | str,
        template_name: str | None = None,
        palette_meta: Any = None,
    ) -> RenderPlan:
        """Build the final RenderPlan based on resolved mode and context."""
        if mode == "latex":
            return RenderPlan(
                name=name,
                mode="latex",
                config=config,
                base_path=base_path,
                tex=None,  # Will be filled by shell layer
                palette_metadata=palette_meta,
            )

        if context is None:
            raise ValueError("HTML render plans require a context dictionary")

        if template_name is None:
            raise ValueError("HTML render plans require a template name")

        return RenderPlan(
            name=name,
            mode="html",
            config=config,
            template_name=template_name,
            context=context,
            base_path=base_path,
            palette_metadata=palette_meta,
        )

    @staticmethod
    def prepare_render_data(
        source_yaml_content: dict[str, Any],
        *,
        preview: bool = False,
        base_path: Path | str = "",
    ) -> RenderPlan:
        """Transform raw resume data into a render plan.

        Args:
            source_yaml_content: Unprocessed resume data from YAML file
            preview: Whether this is for preview mode
            base_path: Base path for resolving assets

        Returns:
            RenderPlan with all necessary information for rendering

        """
        # Get the full normalized config dictionary
        raw_config = source_yaml_content.get("config")
        if not isinstance(raw_config, dict) or not raw_config:
            raise ValueError(
                "Invalid resume config: missing or malformed config section"
            )

        normalized_config_dict, palette_meta, config_for_validation = (
            Resume._normalize_with_palette_fallback(
                raw_config,
                palette_meta_source=source_yaml_content.get("meta"),
            )
        )

        # Validate configuration using our validation
        config = Resume._validate_normalized_config(config_for_validation)

        # Determine render mode
        mode: RenderMode = "latex" if config.output_mode == "latex" else "html"

        # Transform markdown content for HTML mode only
        transformed_data = Resume._transform_for_mode(source_yaml_content, mode)

        name = transformed_data.get("full_name", "resume")

        if mode == "latex":
            return Resume._build_render_plan(
                name,
                mode,
                config,
                context=None,
                base_path=base_path,
                palette_meta=palette_meta,
            )

        template = transformed_data.get("template", "resume_no_bars")
        template_name = f"{template}.html"

        context = dict(transformed_data)
        context["resume_config"] = normalized_config_dict or {}
        context["preview"] = preview

        return Resume._build_render_plan(
            name,
            mode,
            config,
            context,
            base_path=base_path,
            template_name=template_name,
            palette_meta=palette_meta,
        )

    @staticmethod
    def calculate_text_color(background_color: str) -> str:
        """Calculate appropriate text color for given background.

        Args:
            background_color: Hex color string for background

        Returns:
            Hex color string for appropriate text color

        """
        return _get_contrasting_text_color(background_color)

    @staticmethod
    def validate_color(color: str) -> bool:
        """Check if a color string is a valid hex color.

        Args:
            color: Color string to validate

        Returns:
            True if valid hex color, False otherwise

        """
        return _is_valid_color(color)

    @staticmethod
    def calculate_luminance(hex_color: str) -> float:
        """Calculate relative luminance of a hex color.

        Args:
            hex_color: Hex color string

        Returns:
            Luminance value between 0 (darkest) and 1 (lightest)

        """
        rgb = _hex_to_rgb(hex_color)
        return _calculate_luminance(rgb)


__all__ = ["Resume", "ResumeConfig", "RenderPlan", "ValidationResult", "RenderMode"]
