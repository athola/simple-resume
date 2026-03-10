"""Transform LinkedIn profile data into simple-resume YAML schema.

Pure transformation functions -- no I/O, no network calls.
Input is a normalized dict of LinkedIn profile fields; output is a
simple-resume--shaped dict ready for YAML serialization.
"""

from __future__ import annotations

from typing import Any


def _get_str(data: dict[str, Any], key: str) -> str | None:
    """Extract a non-empty stripped string or return None."""
    val = data.get(key)
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


def _normalize_date(raw: str | None) -> str:
    """Return a date string or empty string."""
    if not raw or not isinstance(raw, str):
        return ""
    return raw.strip()


def _convert_header(profile: dict[str, Any]) -> dict[str, Any]:
    """Extract header-level fields from a LinkedIn profile dict."""
    result: dict[str, Any] = {}

    field_map = {
        "full_name": "full_name",
        "name": "full_name",
        "headline": "job_title",
        "job_title": "job_title",
        "email": "email",
        "phone": "phone",
        "website": "web",
        "url": "web",
        "linkedin_url": "linkedin",
        "linkedin": "linkedin",
        "summary": "description",
        "about": "description",
    }

    for src_key, dst_key in field_map.items():
        if dst_key not in result:
            val = _get_str(profile, src_key)
            if val:
                result[dst_key] = val

    location = _get_str(profile, "location")
    if location:
        result["address"] = [location]

    return result


def _convert_experience(
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert LinkedIn experience entries to simple-resume body entries."""
    result: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        title = _get_str(entry, "title") or _get_str(entry, "position") or ""
        company = _get_str(entry, "company") or _get_str(entry, "company_name") or ""
        description = _get_str(entry, "description") or ""
        start = _normalize_date(entry.get("start_date") or entry.get("start"))
        end = _normalize_date(entry.get("end_date") or entry.get("end"))
        if not end:
            end = "Present" if _get_str(entry, "is_current") else ""

        result.append(
            {
                "start": start,
                "end": end,
                "title": title,
                "company": company,
                "description": description,
            }
        )
    return result


def _convert_education(
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert LinkedIn education entries to simple-resume body entries."""
    result: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        degree = _get_str(entry, "degree") or _get_str(entry, "degree_name") or ""
        field = _get_str(entry, "field_of_study") or _get_str(entry, "field") or ""
        title = " ".join(p for p in (degree, field) if p)
        school = _get_str(entry, "school") or _get_str(entry, "school_name") or ""
        description = _get_str(entry, "description") or ""
        start = _normalize_date(entry.get("start_date") or entry.get("start"))
        end = _normalize_date(entry.get("end_date") or entry.get("end"))

        result.append(
            {
                "start": start,
                "end": end,
                "title": title,
                "company": school,
                "description": description,
            }
        )
    return result


def _convert_skills(
    skills: list[Any],
) -> list[str]:
    """Extract skill names from LinkedIn skill entries."""
    result: list[str] = []
    for skill in skills:
        if isinstance(skill, str) and skill.strip():
            result.append(skill.strip())
        elif isinstance(skill, dict):
            name = _get_str(skill, "name") or _get_str(skill, "skill")
            if name:
                result.append(name)
    return sorted(set(result))


def linkedin_to_simple_resume(
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Convert a normalized LinkedIn profile dict to a simple-resume dict.

    Args:
        profile: Normalized LinkedIn profile data with keys like
            ``full_name``, ``headline``, ``experience``, ``education``,
            ``skills``, etc.

    Returns:
        A dict matching the simple-resume YAML schema, ready to be
        serialized with ``yaml.dump()``.

    """
    result: dict[str, Any] = {
        "template": "resume_no_bars",
    }

    # Header fields
    header = _convert_header(profile)
    result.update(header)

    # Body sections
    body: dict[str, list[dict[str, Any]]] = {}

    experience = profile.get("experience")
    if isinstance(experience, list) and experience:
        exp_entries = _convert_experience(experience)
        if exp_entries:
            body["Experience"] = exp_entries

    education = profile.get("education")
    if isinstance(education, list) and education:
        edu_entries = _convert_education(education)
        if edu_entries:
            body["Education"] = edu_entries

    if body:
        result["body"] = body

    # Skills
    skills = profile.get("skills")
    if isinstance(skills, list) and skills:
        keyskills = _convert_skills(skills)
        if keyskills:
            result["keyskills"] = keyskills

    return result


__all__ = ["linkedin_to_simple_resume"]
