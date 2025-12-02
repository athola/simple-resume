"""High-level resume generation module in shell layer.

This module provides a clean, organized interface for generating resumes
in various formats. It offers both standard (eager) and lazy-loading
implementations to optimize for different use cases.

.. versionadded:: 0.1.0

"""

# Direct imports from core generation modules
from simple_resume.core.generate.html import (
    HtmlGeneratorFactory,
    create_html_generator_factory,
)
from simple_resume.core.generate.pdf import (
    PdfGeneratorFactory,
)

# Re-export lazy loading versions for backward compatibility
from simple_resume.shell.generate.lazy import (
    generate,
    generate_all,
    generate_html,
    generate_pdf,
    generate_resume,
    preview,
)

__all__ = [
    "generate",
    "generate_all",
    "generate_html",
    "generate_pdf",
    "generate_resume",
    "preview",
]
