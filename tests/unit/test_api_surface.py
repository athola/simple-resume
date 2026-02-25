"""API surface contract tests."""

from __future__ import annotations

import simple_resume
from tests.bdd import Scenario

EXPECTED_PUBLIC_SYMBOLS = {
    "__version__",
    # Core models (data only)
    "Resume",
    "ResumeConfig",
    "RenderPlan",
    "ValidationResult",
    # Exceptions
    "SimpleResumeError",
    "ValidationError",
    "ConfigurationError",
    "TemplateError",
    "GenerationError",
    "PaletteError",
    "FileSystemError",
    "SessionError",
    # Results & sessions
    "GenerationResult",
    "GenerationMetadata",
    "BatchGenerationResult",
    "ResumeSession",
    "SessionConfig",
    "create_session",
    # Generation primitives
    "GenerationConfig",
    "generate_pdf",
    "generate_html",
    "generate_all",
    "generate_resume",
    # Shell layer I/O functions
    "to_pdf",
    "to_html",
    "resume_generate",
    # Convenience helpers
    "generate",
    "GenerateOptions",
    "preview",
    # ATS scoring (v0.2.0)
    "BaseScorer",
    "ScorerResult",
    "ExtractedEntities",
    "EntityExtractor",
    "extract_entities",
    "TFIDFScorer",
    "JaccardScorer",
    "KeywordScorer",
    "ATSTournament",
    "TournamentResult",
    "score_resume",
    "ATSReportGenerator",
    # LLM infrastructure (v0.3.0)
    "LLMProvider",
    "LLMConfig",
    "LLMError",
    "LLMNotAvailableError",
    # LinkedIn import (v0.3.0)
    "linkedin_to_simple_resume",
    # Job post tailoring (v0.3.0)
    "JobRequirements",
    "GapAnalysis",
    "analyze_gaps",
    "build_tailoring_prompt",
}


def test_public_api_surface_matches_reference(story: Scenario) -> None:
    story.given("the curated __all__ list defines the stable API surface")

    story.when("reading simple_resume.__all__")
    exported = set(simple_resume.__all__)

    story.then("the exported symbols match the reference list exactly")
    assert exported == EXPECTED_PUBLIC_SYMBOLS
    for symbol in exported:
        assert hasattr(simple_resume, symbol)
