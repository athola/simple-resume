"""Tests for LLM prompt templates."""

from __future__ import annotations

from simple_resume.core.llm.prompts import (
    EXTRACT_JOB_REQUIREMENTS_PROMPT,
    GENERATE_COLOR_SCHEME_PROMPT,
    LINKEDIN_ENHANCE_PROMPT,
    TAILOR_RESUME_PROMPT,
)


class TestPromptTemplates:
    def test_tailor_resume_prompt_exists(self):
        assert isinstance(TAILOR_RESUME_PROMPT, str)
        assert len(TAILOR_RESUME_PROMPT) > 0

    def test_tailor_resume_prompt_has_placeholders(self):
        assert "{resume}" in TAILOR_RESUME_PROMPT
        assert "{job_posting}" in TAILOR_RESUME_PROMPT

    def test_extract_job_requirements_prompt_exists(self):
        assert isinstance(EXTRACT_JOB_REQUIREMENTS_PROMPT, str)
        assert len(EXTRACT_JOB_REQUIREMENTS_PROMPT) > 0

    def test_extract_job_requirements_has_placeholder(self):
        assert "{job_posting}" in EXTRACT_JOB_REQUIREMENTS_PROMPT

    def test_linkedin_enhance_prompt_exists(self):
        assert isinstance(LINKEDIN_ENHANCE_PROMPT, str)
        assert len(LINKEDIN_ENHANCE_PROMPT) > 0

    def test_linkedin_enhance_has_placeholder(self):
        assert "{profile_data}" in LINKEDIN_ENHANCE_PROMPT

    def test_generate_color_scheme_prompt_exists(self):
        assert isinstance(GENERATE_COLOR_SCHEME_PROMPT, str)
        assert len(GENERATE_COLOR_SCHEME_PROMPT) > 0

    def test_generate_color_scheme_has_placeholder(self):
        assert "{company_url}" in GENERATE_COLOR_SCHEME_PROMPT

    def test_prompts_are_format_safe(self):
        """Prompts should be formattable with their expected placeholders."""
        result = TAILOR_RESUME_PROMPT.format(
            resume="test resume", job_posting="test job"
        )
        assert "test resume" in result
        assert "test job" in result

        result = EXTRACT_JOB_REQUIREMENTS_PROMPT.format(job_posting="test job")
        assert "test job" in result

        result = LINKEDIN_ENHANCE_PROMPT.format(profile_data="test profile")
        assert "test profile" in result

        result = GENERATE_COLOR_SCHEME_PROMPT.format(company_url="https://example.com")
        assert "https://example.com" in result
