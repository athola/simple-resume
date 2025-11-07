"""API surface contract tests."""

from __future__ import annotations

import simple_resume

EXPECTED_PUBLIC_SYMBOLS = {
    "__version__",
    "Resume",
    "ResumeConfig",
    "RenderPlan",
    "SimpleResumeError",
    "ValidationError",
    "ConfigurationError",
    "TemplateError",
    "GenerationError",
    "PaletteError",
    "FileSystemError",
    "SessionError",
    "GenerationResult",
    "GenerationMetadata",
    "BatchGenerationResult",
    "ResumeSession",
    "SessionConfig",
    "create_session",
    "GenerationConfig",
    "generate_pdf",
    "generate_html",
    "generate_all",
    "generate_resume",
    "generate",
    "preview",
}


def test_public_api_surface_matches_reference(story) -> None:
    story.given("the curated __all__ list defines the stable API surface")

    story.when("reading simple_resume.__all__")
    exported = set(simple_resume.__all__)

    story.then("the exported symbols match the reference list exactly")
    assert exported == EXPECTED_PUBLIC_SYMBOLS
    for symbol in exported:
        assert hasattr(simple_resume, symbol)
