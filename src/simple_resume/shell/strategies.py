"""PDF generation strategies.

This module contains the strategy implementations that coordinate
between core business logic and shell I/O operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..core.models import RenderPlan
from ..core.pdf_generation import LatexGenerationContext, generate_pdf_with_latex
from ..result import GenerationResult
from .rendering_operations import generate_pdf_with_weasyprint


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


class PdfGenerationRequest:
    """Request data for PDF generation."""

    def __init__(
        self,
        render_plan: RenderPlan,
        output_path: Path,
        open_after: bool = False,
        filename: str | None = None,
        resume_name: str = "resume",
    ) -> None:
        self.render_plan = render_plan
        self.output_path = output_path
        self.open_after = open_after
        self.filename = filename
        self.resume_name = resume_name


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
            raw_data=None,  # Will be set by the calling code
            processed_data={},  # Empty dict for now, populated by generation logic
            paths=None,  # Will be set by the calling code
            filename=request.filename,
        )

        # Delegate to the existing LaTeX generation logic
        return generate_pdf_with_latex(
            request.render_plan,
            request.output_path,
            context,
        )[0]

    def get_template_name(self, render_plan: RenderPlan) -> str:
        """Get template name for LaTeX mode."""
        return render_plan.template_name or "latex/basic.tex"


__all__ = [
    "WeasyPrintStrategy",
    "LatexStrategy",
]
