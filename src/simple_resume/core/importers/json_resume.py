"""Import helpers for the JSON Resume (jsonresume.org) open resume format.

This module intentionally does *not* attempt a 1:1 mapping of every JSON Resume
field to simple-resume. Instead, it provides a pragmatic conversion that:

- Produces a valid simple-resume payload (including a non-empty ``config`` block)
- Preserves key content (basics, work, education, projects)
- Uses markdown-friendly formatting for highlights

Schema reference (v1.0.x): https://github.com/jsonresume/resume-schema
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def looks_like_json_resume(payload: Any) -> bool:
    """Return True if payload resembles a JSON Resume document."""
    if not isinstance(payload, Mapping):
        return False
    basics = payload.get("basics")
    return isinstance(basics, Mapping) and "full_name" not in payload


def _strip_url_prefix(url: str, prefix: str) -> str:
    if url.startswith(prefix):
        return url[len(prefix) :].lstrip("/")
    return url


def _to_markdown_bullets(items: Any) -> str:
    if not items:
        return ""
    if isinstance(items, str):
        return items
    if not isinstance(items, list):
        return str(items)
    cleaned = [str(item).strip() for item in items if item]
    if not cleaned:
        return ""
    return "\n".join(f"- {line}" for line in cleaned)


def _join_nonempty(*parts: Any, sep: str = "\n\n") -> str:
    chunks = [str(p).strip() for p in parts if isinstance(p, str) and p.strip()]
    return sep.join(chunks)


def _get_str(data: Mapping[str, Any], key: str) -> str | None:
    """Extract a non-empty stripped string or return None."""
    val = data.get(key)
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


def _convert_basics_simple(basics: Mapping[str, Any], result: dict[str, Any]) -> None:
    """Extract simple scalar fields from basics into result."""
    field_map = {
        "name": "full_name",
        "email": "email",
        "phone": "phone",
        "url": "web",
        "image": "image_uri",
        "label": "headline",
        "summary": "description",
    }
    for src_key, dst_key in field_map.items():
        val = _get_str(basics, src_key)
        if val:
            result[dst_key] = val


def _convert_location(basics: Mapping[str, Any], result: dict[str, Any]) -> None:
    """Extract location from basics into result['address']."""
    location = basics.get("location")
    if not isinstance(location, Mapping):
        return

    address_lines: list[str] = []
    addr = _get_str(location, "address")
    if addr:
        address_lines.append(addr)

    city, region, postal = (
        location.get("city"),
        location.get("region"),
        location.get("postalCode"),
    )
    line2_parts = [
        str(x).strip()
        for x in (city, region, postal)
        if isinstance(x, str) and x.strip()
    ]
    if line2_parts:
        address_lines.append(" ".join(line2_parts))

    country = _get_str(location, "countryCode")
    if country:
        address_lines.append(country)

    if address_lines:
        result["address"] = address_lines


def _convert_profiles(basics: Mapping[str, Any], result: dict[str, Any]) -> None:
    """Extract linkedin/github from profiles into result."""
    profiles = basics.get("profiles")
    if not isinstance(profiles, list):
        return

    for profile in profiles:
        if not isinstance(profile, Mapping):
            continue
        network = str(profile.get("network", "")).strip().lower()
        purl = _get_str(profile, "url")
        username = _get_str(profile, "username")

        if network == "linkedin":
            if purl:
                result["linkedin"] = _strip_url_prefix(
                    purl, "https://www.linkedin.com/"
                )
            elif username:
                result["linkedin"] = username
        elif network == "github":
            if purl:
                result["github"] = _strip_url_prefix(purl, "https://github.com/")
            elif username:
                result["github"] = username


def _convert_work(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Convert work entries to simple-resume format."""
    work = payload.get("work")
    if not isinstance(work, list):
        return []

    entries: list[dict[str, Any]] = []
    for item in work:
        if not isinstance(item, Mapping):
            continue
        highlights = _to_markdown_bullets(item.get("highlights"))
        raw_summary = item.get("summary")
        summary_str = str(raw_summary).strip() if raw_summary else ""
        desc = _join_nonempty(summary_str, highlights)
        entries.append(
            {
                "start": item.get("startDate") or "",
                "end": item.get("endDate") or "",
                "title": item.get("position") or "",
                "company": item.get("name") or "",
                "company_link": item.get("url") or "",
                "description": desc or "",
            }
        )
    return entries


def _convert_education(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Convert education entries to simple-resume format."""
    education = payload.get("education")
    if not isinstance(education, list):
        return []

    entries: list[dict[str, Any]] = []
    for item in education:
        if not isinstance(item, Mapping):
            continue
        study = str(item.get("studyType", "")).strip()
        area = str(item.get("area", "")).strip()
        title = " ".join(x for x in (study, area) if x)

        desc_parts: list[str] = []
        gpa = item.get("gpa")
        if gpa:
            desc_parts.append(f"GPA: {gpa}")
        courses_md = _to_markdown_bullets(item.get("courses"))
        if courses_md:
            desc_parts.append("Courses:\n" + courses_md)

        entries.append(
            {
                "start": item.get("startDate") or "",
                "end": item.get("endDate") or "",
                "title": title,
                "company": item.get("institution") or "",
                "description": _join_nonempty(*desc_parts) or "",
            }
        )
    return entries


def _convert_projects(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Convert project entries to simple-resume format."""
    projects = payload.get("projects")
    if not isinstance(projects, list):
        return []

    entries: list[dict[str, Any]] = []
    for item in projects:
        if not isinstance(item, Mapping):
            continue
        highlights = _to_markdown_bullets(item.get("highlights"))
        raw_desc = item.get("description")
        desc_str = str(raw_desc).strip() if raw_desc else ""
        desc = _join_nonempty(desc_str, highlights)
        entries.append(
            {
                "start": item.get("startDate") or "",
                "end": item.get("endDate") or "",
                "title": item.get("name") or "",
                "title_link": item.get("url") or "",
                "company": item.get("entity") or "",
                "description": desc or "",
            }
        )
    return entries


def _convert_skills(payload: Mapping[str, Any], result: dict[str, Any]) -> None:
    """Extract skills into expertise and keyskills."""
    skills = payload.get("skills")
    if not isinstance(skills, list):
        return

    expertise: list[str] = []
    keyskills: list[str] = []
    for group in skills:
        if not isinstance(group, Mapping):
            continue
        group_name = _get_str(group, "name")
        if group_name:
            expertise.append(group_name)
        keywords = group.get("keywords")
        if isinstance(keywords, list):
            for kw in keywords:
                if isinstance(kw, str) and kw.strip():
                    keyskills.append(kw.strip())

    if expertise:
        result["expertise"] = sorted(set(expertise))
    if keyskills:
        result["keyskills"] = sorted(set(keyskills))


def json_resume_to_simple_resume(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a JSON Resume payload into a simple-resume YAML-shaped dict."""
    basics = payload.get("basics")
    basics = basics if isinstance(basics, Mapping) else {}

    result: dict[str, Any] = {
        "template": "resume_no_bars",
        "config": {"template": "resume_no_bars"},
    }

    # Convert basics section
    _convert_basics_simple(basics, result)
    _convert_location(basics, result)
    _convert_profiles(basics, result)

    # Build body sections
    body: dict[str, list[dict[str, Any]]] = {}
    work_entries = _convert_work(payload)
    if work_entries:
        body["Experience"] = work_entries
    education_entries = _convert_education(payload)
    if education_entries:
        body["Education"] = education_entries
    project_entries = _convert_projects(payload)
    if project_entries:
        body["Projects"] = project_entries
    if body:
        result["body"] = body

    # Convert skills
    _convert_skills(payload, result)

    return result


__all__ = ["json_resume_to_simple_resume", "looks_like_json_resume"]
