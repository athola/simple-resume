"""Read and parse LinkedIn profile data from files.

Shell layer module -- performs file I/O and HTML parsing.
Produces a normalized profile dict suitable for the pure
``core.importers.linkedin.linkedin_to_simple_resume`` transformer.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

# Line indices for plain-text header fields
_NAME_LINE = 0
_HEADLINE_LINE = 1
_LOCATION_LINE = 2
_MIN_HEADER_LINES = 3


def _extract_html_header(soup: BeautifulSoup, profile: dict[str, Any]) -> None:
    """Extract name, headline, and location from HTML header."""
    h1 = soup.find("h1")
    if h1:
        name = h1.get_text(strip=True)
        if name:
            profile["full_name"] = name

    headline_el = soup.find(class_="text-body-medium")
    if headline_el:
        headline = headline_el.get_text(strip=True)
        if headline:
            profile["headline"] = headline

    location_el = soup.find(class_="text-body-small")
    if location_el:
        location = location_el.get_text(strip=True)
        if location:
            profile["location"] = location


def _extract_html_about(soup: BeautifulSoup, profile: dict[str, Any]) -> None:
    """Extract the about/summary section from HTML."""
    about_section = soup.find("section", id="about")
    if about_section:
        about_text = about_section.get_text(strip=True)
        if about_text:
            profile["summary"] = about_text


def _parse_experience_item(item: Tag) -> dict[str, Any]:
    """Parse a single experience list item from HTML."""
    entry: dict[str, Any] = {}
    title_el = item.find(class_="title")
    if title_el:
        entry["title"] = title_el.get_text(strip=True)
    company_el = item.find(class_="company")
    if company_el:
        entry["company"] = company_el.get_text(strip=True)
    date_el = item.find(class_="date-range")
    if date_el:
        _parse_date_range(date_el.get_text(strip=True), entry)
    desc_el = item.find(class_="description")
    if desc_el:
        entry["description"] = desc_el.get_text(strip=True)
    return entry


def _extract_html_experience(soup: BeautifulSoup, profile: dict[str, Any]) -> None:
    """Extract the experience section from HTML."""
    exp_section = soup.find("section", id="experience")
    if not exp_section:
        return
    entries: list[dict[str, Any]] = []
    for item in exp_section.find_all("li"):
        entry = _parse_experience_item(item)
        if entry:
            entries.append(entry)
    if entries:
        profile["experience"] = entries


def extract_profile_from_html(html: str) -> dict[str, Any]:
    """Parse LinkedIn HTML and extract profile fields.

    Args:
        html: Raw HTML string from a LinkedIn profile page.

    Returns:
        Normalized profile dict with keys like ``full_name``,
        ``headline``, ``location``, ``experience``, etc.

    """
    soup = BeautifulSoup(html, "html.parser")
    profile: dict[str, Any] = {}
    _extract_html_header(soup, profile)
    _extract_html_about(soup, profile)
    _extract_html_experience(soup, profile)
    return profile


def _parse_date_range(date_text: str, entry: dict[str, Any]) -> None:
    """Parse a date range string like 'Jan 2020 - Present'."""
    parts = re.split(r"\s*[-\u2013]\s*", date_text, maxsplit=1)
    if parts:
        entry["start_date"] = parts[0].strip()
    if len(parts) > 1:
        end = parts[1].strip()
        entry["end_date"] = end
        if end.lower() == "present":
            entry["is_current"] = "true"


def extract_profile_from_text(text: str) -> dict[str, Any]:
    """Parse a plain-text LinkedIn profile export.

    Expects a simple structure where the first line is the name,
    second line is the headline, third line is the location, and
    sections are delimited by known headers (About, Experience,
    Education, Skills).

    Args:
        text: Plain text content from a LinkedIn profile.

    Returns:
        Normalized profile dict.

    """
    if not text or not text.strip():
        return {}

    lines = [line.strip() for line in text.strip().split("\n")]
    profile: dict[str, Any] = {}

    _extract_text_header(lines, profile)

    # Parse sections
    sections = _split_sections(lines)

    if "About" in sections:
        about = "\n".join(sections["About"]).strip()
        if about:
            profile["summary"] = about

    if "Experience" in sections:
        profile["experience"] = _parse_text_experience(sections["Experience"])
    if "Education" in sections:
        profile["education"] = _parse_text_education(sections["Education"])
    if "Skills" in sections:
        profile["skills"] = _parse_text_skills(sections["Skills"])

    return profile


def _extract_text_header(lines: list[str], profile: dict[str, Any]) -> None:
    """Extract name, headline, location from the first 3 lines."""
    if len(lines) > _NAME_LINE and lines[_NAME_LINE]:
        profile["full_name"] = lines[_NAME_LINE]
    if len(lines) > _HEADLINE_LINE and lines[_HEADLINE_LINE]:
        profile["headline"] = lines[_HEADLINE_LINE]
    if len(lines) >= _MIN_HEADER_LINES and lines[_LOCATION_LINE]:
        profile["location"] = lines[_LOCATION_LINE]


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    """Split text lines into named sections."""
    section_headers = {"About", "Experience", "Education", "Skills"}
    sections: dict[str, list[str]] = {}
    current_section: str | None = None

    for line in lines:
        if line in section_headers:
            current_section = line
            sections[current_section] = []
        elif current_section is not None:
            sections[current_section].append(line)

    return sections


def _parse_text_experience(
    lines: list[str],
) -> list[dict[str, Any]]:
    """Parse experience lines into structured entries."""
    entries: list[dict[str, Any]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line:
            i += 1
            continue
        match = re.match(r"^(.+?)\s+at\s+(.+)$", line)
        if match:
            entry: dict[str, Any] = {
                "title": match.group(1).strip(),
                "company": match.group(2).strip(),
            }
            i = _consume_date_and_desc(lines, i, entry)
            entries.append(entry)
        i += 1
    return entries


def _consume_date_and_desc(lines: list[str], i: int, entry: dict[str, Any]) -> int:
    """Consume optional date range and description lines after a heading."""
    if i + 1 < len(lines) and lines[i + 1]:
        date_line = lines[i + 1]
        if re.search(r"\d{4}", date_line):
            _parse_date_range(date_line, entry)
            i += 1
    if i + 1 < len(lines) and lines[i + 1]:
        next_line = lines[i + 1]
        if not re.match(r"^(.+?)\s+at\s+(.+)$", next_line):
            entry["description"] = next_line
            i += 1
    return i


def _parse_text_education(
    lines: list[str],
) -> list[dict[str, Any]]:
    """Parse education lines into structured entries."""
    entries: list[dict[str, Any]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line:
            i += 1
            continue
        match = re.match(r"^(.+?)\s+at\s+(.+)$", line)
        if match:
            degree_field = match.group(1).strip()
            school = match.group(2).strip()
            entry = _build_education_entry(degree_field, school)
            if i + 1 < len(lines) and lines[i + 1]:
                date_line = lines[i + 1]
                if re.search(r"\d{4}", date_line):
                    _parse_date_range(date_line, entry)
                    i += 1
            entries.append(entry)
        i += 1
    return entries


def _build_education_entry(degree_field: str, school: str) -> dict[str, Any]:
    """Build an education entry dict, splitting degree from field."""
    degree_match = re.match(
        r"^(B\.S\.|M\.S\.|Ph\.D\.|B\.A\.|M\.A\.|MBA)\s*(.*)",
        degree_field,
    )
    entry: dict[str, Any] = {"school": school}
    if degree_match:
        entry["degree"] = degree_match.group(1).strip()
        entry["field_of_study"] = degree_match.group(2).strip()
    else:
        entry["field_of_study"] = degree_field
    return entry


def _parse_text_skills(lines: list[str]) -> list[str]:
    """Parse skills lines into a flat list."""
    skills: list[str] = []
    for line in lines:
        if not line:
            continue
        for raw_skill in re.split(r"[,;]", line):
            cleaned = raw_skill.strip()
            if cleaned:
                skills.append(cleaned)
    return skills


def read_linkedin_file(path: str) -> dict[str, Any]:
    """Read a LinkedIn profile from a file and extract profile data.

    Supports ``.html`` and ``.txt`` file formats.

    Args:
        path: Path to the LinkedIn profile file.

    Returns:
        Normalized profile dict.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is not supported.

    """
    file_path = Path(path)
    if not file_path.exists():
        msg = f"File not found: {path}"
        raise FileNotFoundError(msg)

    suffix = file_path.suffix.lower()
    content = file_path.read_text(encoding="utf-8")

    if suffix in (".html", ".htm"):
        return extract_profile_from_html(content)
    if suffix == ".txt":
        return extract_profile_from_text(content)

    msg = f"Unsupported file format: {suffix}. Use .html or .txt"
    raise ValueError(msg)


__all__ = [
    "extract_profile_from_html",
    "extract_profile_from_text",
    "read_linkedin_file",
]
