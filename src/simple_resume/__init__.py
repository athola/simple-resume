#!/usr/bin/env python3
"""Public package exports for simple-resume.

This module provides the main public API for simple-resume. The API is organized
by functionality to make it discoverable and intuitive to use.

Core Classes:
    Resume: Main resume data structure with fluent interface
    ResumeConfig: Configuration data for resume rendering
    RenderPlan: Rendering instructions for HTML/LaTeX output
    ValidationResult: Result of resume data validation

Generation Functions:
    generate_pdf: Generate PDF resumes from YAML data
    generate_html: Generate HTML resumes from YAML data
    generate_all: Generate all supported formats

Session Management:
    ResumeSession: Context manager for consistent configuration
    GenerationResult: Rich result objects with metadata

Utility Functions:
    get_content: Load and parse resume data from YAML
    validate_config: Validate resume configuration
    calculate_text_color: Calculate appropriate text colors
    calculate_luminance: Calculate color luminance

Palette System:
    Palette: Color palette management
    get_palette: Get color palettes by name or generate
"""

from __future__ import annotations

# Core classes
from .core.resume import RenderPlan, Resume, ResumeConfig, ValidationResult

# Exception hierarchy
from .exceptions import (
    ConfigurationError,
    FileSystemError,
    GenerationError,
    PaletteError,
    SessionError,
    SimpleResumeError,
    TemplateError,
    ValidationError,
)

# New unified generation API
from .generation import (
    GenerationConfig,
    generate_all,
    generate_html,
    generate_pdf,
    generate_resume,
)

# Rich result objects
from .result import BatchGenerationResult, GenerationMetadata, GenerationResult

# Session management
from .session import ResumeSession, SessionConfig, create_session

# Utility functions
from .utilities import (
    calculate_luminance,
    calculate_text_color,
    get_content,
    normalize_config,
    render_markdown_content,
    validate_config,
)

# Version
__version__ = "0.1.0"

# Public API exports - organized by functionality
__all__ = [
    # Version
    "__version__",
    # Core classes
    "Resume",
    "ResumeConfig",
    "RenderPlan",
    "ValidationResult",
    # Exception hierarchy
    "SimpleResumeError",
    "ValidationError",
    "ConfigurationError",
    "TemplateError",
    "GenerationError",
    "PaletteError",
    "FileSystemError",
    "SessionError",
    # Rich result objects
    "GenerationResult",
    "GenerationMetadata",
    "BatchGenerationResult",
    # Session management
    "ResumeSession",
    "SessionConfig",
    "create_session",
    # Generation functions (new unified API)
    "GenerationConfig",
    "generate_pdf",
    "generate_html",
    "generate_all",
    "generate_resume",
    # Utility functions
    "get_content",
    "validate_config",
    "calculate_text_color",
    "calculate_luminance",
    "render_markdown_content",
    "normalize_config",
]
