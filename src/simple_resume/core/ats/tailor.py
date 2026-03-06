"""Job post gap analysis and resume tailoring logic.

Pure functions -- no I/O, no LLM calls. Analyzes the overlap between
a resume dict and structured job requirements, producing a gap report
and a prompt suitable for LLM-based tailoring.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from simple_resume.core.llm.prompts import TAILOR_RESUME_PROMPT


@dataclass(frozen=True)
class JobRequirements:
    """Structured representation of a job posting's requirements.

    Attributes:
        title: Job title.
        company: Company name.
        required_skills: Skills marked as required.
        preferred_skills: Nice-to-have skills.
        keywords: Important keywords and phrases from the posting.
        experience_years: Minimum years of experience, or None.
        education: Required education level, or None.

    """

    title: str
    company: str = ""
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    experience_years: int | None = None
    education: str | None = None


@dataclass(frozen=True)
class GapAnalysis:
    """Result of comparing a resume against job requirements.

    Attributes:
        matched_required_skills: Required skills found in the resume.
        missing_required_skills: Required skills not found in the resume.
        matched_preferred_skills: Preferred skills found in the resume.
        missing_preferred_skills: Preferred skills not found.
        matched_keywords: Keywords found in the resume content.
        missing_keywords: Keywords not found in the resume content.
        match_score: Overall match score between 0.0 and 1.0.
        summary: Human-readable summary of the analysis.

    """

    matched_required_skills: list[str]
    missing_required_skills: list[str]
    matched_preferred_skills: list[str]
    missing_preferred_skills: list[str]
    matched_keywords: list[str]
    missing_keywords: list[str]
    match_score: float
    summary: str


def _collect_scalar_fields(resume: dict[str, Any], parts: list[str]) -> None:
    """Collect scalar text fields from the resume header."""
    for key in ("full_name", "job_title", "description", "headline"):
        val = resume.get(key)
        if isinstance(val, str):
            parts.append(val)

    keyskills = resume.get("keyskills")
    if isinstance(keyskills, list):
        parts.extend(str(s) for s in keyskills)


def _collect_expertise(resume: dict[str, Any], parts: list[str]) -> None:
    """Collect expertise fields (dict or list) from the resume."""
    expertise = resume.get("expertise")
    if isinstance(expertise, dict):
        for key, val in expertise.items():
            parts.append(str(key))
            if isinstance(val, list):
                parts.extend(str(v) for v in val)
    elif isinstance(expertise, list):
        parts.extend(str(e) for e in expertise)


def _collect_body(resume: dict[str, Any], parts: list[str]) -> None:
    """Collect text from resume body section entries."""
    body = resume.get("body")
    if not isinstance(body, dict):
        return
    for section_entries in body.values():
        if not isinstance(section_entries, list):
            continue
        for entry in section_entries:
            if isinstance(entry, dict):
                parts.extend(val for val in entry.values() if isinstance(val, str))


def _extract_resume_text(resume: dict[str, Any]) -> str:
    """Flatten a resume dict into searchable text."""
    parts: list[str] = []
    _collect_scalar_fields(resume, parts)
    _collect_expertise(resume, parts)
    _collect_body(resume, parts)
    return " ".join(parts).lower()


def _check_skills(skills: list[str], resume_text: str) -> tuple[list[str], list[str]]:
    """Partition skills into matched and missing lists."""
    matched: list[str] = []
    missing: list[str] = []
    for skill in skills:
        if skill.lower() in resume_text:
            matched.append(skill)
        else:
            missing.append(skill)
    return matched, missing


@dataclass
class _SkillCounts:
    """Container for matched/total skill counts for score computation."""

    matched: int
    total: int
    weight: float


def _compute_score(counts: list[_SkillCounts]) -> float:
    """Compute a weighted match score between 0.0 and 1.0."""
    active = [c for c in counts if c.total > 0]
    if not active:
        return 0.0

    weighted = sum(c.weight * (c.matched / c.total) for c in active)
    return round(weighted / sum(c.weight for c in active), 3)


def _build_summary(  # noqa: PLR0913
    score: float,
    matched_req: list[str],
    missing_req: list[str],
    matched_pref: list[str],
    missing_pref: list[str],
    matched_kw: list[str],
    missing_kw: list[str],
    requirements: JobRequirements,
) -> str:
    """Build a human-readable gap analysis summary."""
    n_req = len(requirements.required_skills)
    n_pref = len(requirements.preferred_skills)
    n_kw = len(requirements.keywords)

    lines: list[str] = [
        f"Match score: {score:.0%}",
        f"Required skills: {len(matched_req)}/{n_req} matched",
    ]
    if missing_req:
        lines.append(f"  Missing: {', '.join(missing_req)}")
    if requirements.preferred_skills:
        lines.append(f"Preferred: {len(matched_pref)}/{n_pref} matched")
    if missing_pref:
        lines.append(f"  Missing: {', '.join(missing_pref)}")
    if requirements.keywords:
        lines.append(f"Keywords: {len(matched_kw)}/{n_kw} matched")
    if missing_kw:
        lines.append(f"  Missing: {', '.join(missing_kw)}")
    return "\n".join(lines)


def analyze_gaps(
    resume: dict[str, Any],
    requirements: JobRequirements,
) -> GapAnalysis:
    """Analyze gaps between a resume and job requirements.

    Args:
        resume: Simple-resume format dict.
        requirements: Structured job requirements.

    Returns:
        A GapAnalysis with matched/missing skills, keywords, and a score.

    """
    resume_text = _extract_resume_text(resume)

    matched_req, missing_req = _check_skills(requirements.required_skills, resume_text)
    matched_pref, missing_pref = _check_skills(
        requirements.preferred_skills, resume_text
    )
    matched_kw, missing_kw = _check_skills(requirements.keywords, resume_text)

    score = _compute_score(
        [
            _SkillCounts(len(matched_req), len(requirements.required_skills), 0.5),
            _SkillCounts(len(matched_pref), len(requirements.preferred_skills), 0.2),
            _SkillCounts(len(matched_kw), len(requirements.keywords), 0.3),
        ]
    )

    summary = _build_summary(
        score,
        matched_req,
        missing_req,
        matched_pref,
        missing_pref,
        matched_kw,
        missing_kw,
        requirements,
    )

    return GapAnalysis(
        matched_required_skills=matched_req,
        missing_required_skills=missing_req,
        matched_preferred_skills=matched_pref,
        missing_preferred_skills=missing_pref,
        matched_keywords=matched_kw,
        missing_keywords=missing_kw,
        match_score=score,
        summary=summary,
    )


def build_tailoring_prompt(
    resume: dict[str, Any],
    job_posting_text: str,
) -> str:
    """Build an LLM prompt for resume tailoring.

    Args:
        resume: Simple-resume format dict.
        job_posting_text: Raw text of the job posting.

    Returns:
        A formatted prompt string ready for LLM completion.

    """
    resume_str = json.dumps(resume, indent=2, default=str)
    return TAILOR_RESUME_PROMPT.format(
        resume=resume_str,
        job_posting=job_posting_text,
    )


__all__ = [
    "GapAnalysis",
    "JobRequirements",
    "analyze_gaps",
    "build_tailoring_prompt",
]
