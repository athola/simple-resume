"""Core LLM abstractions (pure, no I/O)."""

from simple_resume.core.llm.prompts import (
    EXTRACT_JOB_REQUIREMENTS_PROMPT,
    GENERATE_COLOR_SCHEME_PROMPT,
    LINKEDIN_ENHANCE_PROMPT,
    TAILOR_RESUME_PROMPT,
)
from simple_resume.core.llm.protocol import LLMConfig, LLMProvider

__all__ = [
    "LLMConfig",
    "LLMProvider",
    "EXTRACT_JOB_REQUIREMENTS_PROMPT",
    "GENERATE_COLOR_SCHEME_PROMPT",
    "LINKEDIN_ENHANCE_PROMPT",
    "TAILOR_RESUME_PROMPT",
]
