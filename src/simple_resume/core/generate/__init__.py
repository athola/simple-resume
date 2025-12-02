"""Core generation functionality for resumes.

This module provides pure functions for generating different output formats
from resume data without any I/O side effects.
"""

from __future__ import annotations

from simple_resume.core.generate.html import create_html_generator_factory
from simple_resume.core.generate.pdf import (
    prepare_pdf_with_latex,
    prepare_pdf_with_weasyprint,
)
from simple_resume.core.generate.plan import build_generation_plan

__all__ = [
    "build_generation_plan",
    "create_html_generator_factory",
    "prepare_pdf_with_latex",
    "prepare_pdf_with_weasyprint",
]
