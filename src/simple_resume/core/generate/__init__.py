"""Core generation functionality for resumes.

This module provides pure functions for generating different output formats
from resume data without any I/O side effects.
"""

from __future__ import annotations

from .html import prepare_html_with_jinja
from .pdf import prepare_pdf_with_latex, prepare_pdf_with_weasyprint
from .plan import build_generation_plan

__all__ = [
    "build_generation_plan",
    "prepare_html_with_jinja",
    "prepare_pdf_with_latex",
    "prepare_pdf_with_weasyprint",
]
