"""PDF generation strategies.

This module contains the strategy implementations that coordinate
between core business logic and shell I/O operations.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from simple_resume.core.exceptions import GenerationError
from simple_resume.core.generate.pdf import prepare_pdf_with_latex
from simple_resume.core.latex.types import LatexGenerationContext
from simple_resume.core.models import RenderPlan
from simple_resume.core.paths import Paths
from simple_resume.core.result import GenerationResult
from simple_resume.shell.effect_executor import EffectExecutor
from simple_resume.shell.render.latex import LatexCompilationError
from simple_resume.shell.render.operations import generate_pdf_with_weasyprint


class PdfGenerationStrategy(ABC):
    """Abstract base class for PDF generation strategies."""

    @abstractmethod
    def generate_pdf(self, request: Any) -> GenerationResult:
        """Generate PDF using the specific strategy."""
        pass

    @abstractmethod
    def get_template_name(self, render_plan: RenderPlan) -> str:
        """Get the template name for metadata purposes."""
        pass


@dataclass(slots=True)
class PdfGenerationRequest:
    """Request data for PDF generation."""

    render_plan: RenderPlan
    output_path: Path
    open_after: bool = False
    filename: str | None = None
    resume_name: str = "resume"
    raw_data: dict[str, Any] | None = None
    processed_data: dict[str, Any] | None = None
    paths: Paths | None = None


class WeasyPrintStrategy(PdfGenerationStrategy):
    """PDF generation strategy using WeasyPrint backend."""

    def generate_pdf(self, request: PdfGenerationRequest) -> GenerationResult:
        """Generate PDF using WeasyPrint backend."""
        result, _ = generate_pdf_with_weasyprint(
            request.render_plan,
            request.output_path,
            resume_name=request.resume_name,
            filename=request.filename,
        )

        # Open file if requested
        if request.open_after and result.exists:
            try:
                # Robustly obtain a filesystem-safe string without instantiating
                # platform-specific Path subclasses (e.g., WindowsPath) on
                # non-Windows CI runners that patch os.name/sys.platform.
                try:
                    path_to_open = os.fspath(result.output_path)
                except (TypeError, AttributeError, NotImplementedError):
                    path_to_open = str(result.output_path)
                if sys.platform.startswith("darwin"):
                    opener = shutil.which("open") or "open"
                    subprocess.Popen(  # noqa: S603  # nosec B603
                        [opener, path_to_open],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                elif os.name == "nt":
                    os.startfile(path_to_open)  # type: ignore[attr-defined]  # noqa: S606  # nosec B606
                else:
                    opener = shutil.which("xdg-open")
                    if opener:
                        subprocess.Popen(  # noqa: S603  # nosec B603
                            [opener, path_to_open],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
            except Exception as exc:  # noqa: BLE001
                print(f"Warning: Could not open file: {exc}", file=sys.stderr)

        return result

    def get_template_name(self, render_plan: RenderPlan) -> str:
        """Get template name for WeasyPrint mode."""
        return render_plan.template_name or "unknown"


class LatexStrategy(PdfGenerationStrategy):
    """PDF generation strategy using LaTeX backend."""

    def generate_pdf(self, request: PdfGenerationRequest) -> GenerationResult:
        """Generate PDF using LaTeX backend."""
        # Create generation context
        context = LatexGenerationContext(
            resume_data=request.raw_data,
            processed_data=request.processed_data or {},
            output_path=request.output_path,
            filename=request.filename,
            paths=request.paths,
        )

        # Prepare LaTeX generation (pure function returns effects)
        try:
            tex_content, effects, metadata = prepare_pdf_with_latex(
                request.render_plan,
                request.output_path,
                context,
            )

            # Execute the effects to create files and run pdflatex
            executor = EffectExecutor()
            executor.execute_many(effects)

        except LatexCompilationError as exc:
            # Convert shell-layer exception to core-layer exception
            raise GenerationError(
                f"LaTeX compilation failed: {exc}",
                output_path=request.output_path,
                format_type="pdf",
                resume_name=request.resume_name,
            ) from exc

        # Create result from metadata
        generation_result = GenerationResult(
            output_path=request.output_path,
            format_type="pdf",
            metadata=metadata,
        )

        # Open file if requested
        if request.open_after and generation_result.output_path.exists():
            try:
                if sys.platform.startswith("darwin"):
                    opener = shutil.which("open") or "open"
                    subprocess.Popen(  # noqa: S603  # nosec B603
                        [opener, str(generation_result.output_path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                elif os.name == "nt":
                    os.startfile(str(generation_result.output_path))  # type: ignore[attr-defined]  # noqa: S606  # nosec B606
                else:
                    opener = shutil.which("xdg-open")
                    if opener:
                        subprocess.Popen(  # noqa: S603  # nosec B603
                            [opener, str(generation_result.output_path)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
            except Exception as exc:  # noqa: BLE001
                print(f"Warning: Could not open file: {exc}", file=sys.stderr)

        return generation_result

    def get_template_name(self, render_plan: RenderPlan) -> str:
        """Get template name for LaTeX mode."""
        return render_plan.template_name or "latex/basic.tex"


__all__ = [
    "WeasyPrintStrategy",
    "LatexStrategy",
]
