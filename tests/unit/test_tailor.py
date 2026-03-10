"""Tests for job post tailoring core module.

Feature: Resume Tailoring
    As a job seeker
    I want to analyze gaps between my resume and a job posting
    So that I can tailor my resume for better ATS matching
"""

from __future__ import annotations

from simple_resume.core.ats.tailor import (
    JobRequirements,
    analyze_gaps,
    build_tailoring_prompt,
)


def _make_requirements(**overrides: object) -> JobRequirements:
    """Build a minimal JobRequirements with optional overrides."""
    defaults = {
        "title": "Senior Software Engineer",
        "company": "Acme Corp",
        "required_skills": ["Python", "AWS", "Docker"],
        "preferred_skills": ["Kubernetes", "Go"],
        "keywords": ["microservices", "REST API", "CI/CD"],
    }
    defaults.update(overrides)
    return JobRequirements(**defaults)


def _make_resume_data() -> dict:
    """Build a minimal simple-resume dict."""
    return {
        "full_name": "Jane Doe",
        "job_title": "Software Engineer",
        "keyskills": ["Python", "Docker", "JavaScript", "React"],
        "description": "Built REST API services over 5 years.",
        "body": {
            "Experience": [
                {
                    "title": "Software Engineer",
                    "company": "Startup Inc",
                    "description": "Built microservices with Python and Docker.",
                }
            ]
        },
    }


class TestJobRequirements:
    """Scenario group: JobRequirements dataclass behavior."""

    def test_create_with_required_fields(self):
        """Given required fields, create a valid JobRequirements."""
        reqs = _make_requirements()
        assert reqs.title == "Senior Software Engineer"
        assert reqs.company == "Acme Corp"
        assert "Python" in reqs.required_skills

    def test_defaults_for_optional_fields(self):
        """Given only title, other fields default to empty."""
        reqs = JobRequirements(title="Engineer")
        assert reqs.company == ""
        assert reqs.required_skills == []
        assert reqs.preferred_skills == []
        assert reqs.keywords == []
        assert reqs.experience_years is None
        assert reqs.education is None


class TestAnalyzeGaps:
    """Scenario group: analyzing gaps between resume and job requirements."""

    def test_identifies_missing_required_skills(self):
        """Given a resume missing required skills, they appear in gaps."""
        reqs = _make_requirements()
        resume = _make_resume_data()
        analysis = analyze_gaps(resume, reqs)
        assert "AWS" in analysis.missing_required_skills

    def test_identifies_present_required_skills(self):
        """Given a resume with required skills, they appear in matched."""
        reqs = _make_requirements()
        resume = _make_resume_data()
        analysis = analyze_gaps(resume, reqs)
        assert "Python" in analysis.matched_required_skills
        assert "Docker" in analysis.matched_required_skills

    def test_identifies_missing_preferred_skills(self):
        """Given a resume missing preferred skills, they appear in gaps."""
        reqs = _make_requirements()
        resume = _make_resume_data()
        analysis = analyze_gaps(resume, reqs)
        assert "Kubernetes" in analysis.missing_preferred_skills

    def test_identifies_matched_keywords(self):
        """Given resume content with job keywords, they appear in matched."""
        reqs = _make_requirements()
        resume = _make_resume_data()
        analysis = analyze_gaps(resume, reqs)
        assert "microservices" in analysis.matched_keywords
        assert "REST API" in analysis.matched_keywords

    def test_score_between_zero_and_one(self):
        """Gap analysis score is always between 0.0 and 1.0."""
        reqs = _make_requirements()
        resume = _make_resume_data()
        analysis = analyze_gaps(resume, reqs)
        assert 0.0 <= analysis.match_score <= 1.0

    def test_perfect_match_scores_high(self):
        """Given all skills and keywords present, score is high."""
        reqs = JobRequirements(
            title="Engineer",
            required_skills=["Python"],
            keywords=["microservices"],
        )
        resume = _make_resume_data()
        analysis = analyze_gaps(resume, reqs)
        assert analysis.match_score >= 0.8

    def test_no_match_scores_low(self):
        """Given no matching skills or keywords, score is low."""
        reqs = JobRequirements(
            title="Data Scientist",
            required_skills=["R", "TensorFlow", "Spark"],
            preferred_skills=["Hadoop"],
            keywords=["machine learning", "statistical modeling"],
        )
        resume = _make_resume_data()
        analysis = analyze_gaps(resume, reqs)
        assert analysis.match_score <= 0.3

    def test_empty_resume_returns_all_gaps(self):
        """Given an empty resume, all requirements are gaps."""
        reqs = _make_requirements()
        analysis = analyze_gaps({}, reqs)
        assert len(analysis.missing_required_skills) == 3
        assert analysis.match_score == 0.0

    def test_gap_analysis_has_summary(self):
        """Gap analysis includes a human-readable summary string."""
        reqs = _make_requirements()
        resume = _make_resume_data()
        analysis = analyze_gaps(resume, reqs)
        assert isinstance(analysis.summary, str)
        assert len(analysis.summary) > 0


class TestBuildTailoringPrompt:
    """Scenario group: constructing the LLM prompt for tailoring."""

    def test_prompt_contains_resume_data(self):
        """Given resume data, it appears in the tailoring prompt."""
        resume = _make_resume_data()
        job_text = "We need a Python developer."
        prompt = build_tailoring_prompt(resume, job_text)
        assert "Jane Doe" in prompt
        assert "Python" in prompt

    def test_prompt_contains_job_posting(self):
        """Given a job posting, it appears in the tailoring prompt."""
        resume = _make_resume_data()
        job_text = "Looking for a Kubernetes expert."
        prompt = build_tailoring_prompt(resume, job_text)
        assert "Kubernetes expert" in prompt

    def test_prompt_is_nonempty_string(self):
        """Prompt is always a non-empty string."""
        prompt = build_tailoring_prompt({}, "")
        assert isinstance(prompt, str)
        assert len(prompt) > 0
