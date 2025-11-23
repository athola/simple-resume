"""LaTeX section preparation functions (pure, no side effects)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from simple_resume.core.latex.conversion import collect_blocks, convert_inline
from simple_resume.core.latex.escaping import escape_latex, escape_url
from simple_resume.core.latex.formatting import format_date, linkify
from simple_resume.core.latex.types import LatexEntry, LatexSection
from simple_resume.core.skills import format_skill_groups


def build_contact_lines(data: dict[str, Any]) -> list[str]:
    """Build contact information lines from resume data.

    This is a pure function that transforms resume data into LaTeX-formatted
    contact lines with FontAwesome icons.

    Args:
        data: Resume data dictionary containing contact fields.

    Returns:
        List of LaTeX-formatted contact lines.

    Examples:
        >>> data = {"email": "user@example.com", "phone": "555-1234"}
        >>> lines = build_contact_lines(data)
        >>> len(lines)
        2

    """
    lines: list[str] = []

    def _icon_prefix(icon: str) -> str:
        return rf"\{icon}\enspace "

    # Address handling
    address = data.get("address")
    if isinstance(address, Iterable) and not isinstance(address, (str, bytes)):
        joined = ", ".join(str(part) for part in address if part)
    elif address:
        joined = str(address)
    else:
        joined = ""

    if joined:
        lines.append(f"{_icon_prefix('faLocation')}{convert_inline(joined)}")

    # Phone
    phone = data.get("phone")
    if phone:
        lines.append(f"{_icon_prefix('faPhone')}{escape_latex(str(phone))}")

    # Email
    email = data.get("email")
    if email:
        lines.append(
            rf"{_icon_prefix('faEnvelope')}\href{{mailto:{escape_url(email)}}}{{\nolinkurl{{{escape_latex(email)}}}}}"
        )

    # GitHub
    github_added = False
    github = data.get("github")
    if github:
        gh_value = str(github)
        gh_url = (
            gh_value
            if gh_value.startswith("http")
            else f"https://github.com/{gh_value.lstrip('/')}"
        )
        lines.append(
            rf"{_icon_prefix('faGithub')}\href{{{escape_url(gh_url)}}}{{\nolinkurl{{{escape_latex(gh_value)}}}}}"
        )
        github_added = True

    # Web
    web = data.get("web")
    if web:
        web_value = str(web)
        icon = "faGithub" if "github.com" in web_value.lower() else "faGlobe"
        if icon == "faGithub" and github_added:
            pass  # Skip duplicate GitHub entry
        else:
            lines.append(
                rf"{_icon_prefix(icon)}\href{{{escape_url(web_value)}}}{{\nolinkurl{{{escape_latex(web_value)}}}}}"
            )

    # LinkedIn
    linkedin = data.get("linkedin")
    if linkedin:
        url = linkedin
        if not url.startswith("http"):
            url = f"https://www.linkedin.com/{linkedin.lstrip('/')}"
        lines.append(
            rf"{_icon_prefix('faLinkedin')}\href{{{escape_url(url)}}}{{\nolinkurl{{{escape_latex(linkedin)}}}}}"
        )

    return lines


def prepare_sections(data: dict[str, Any]) -> list[LatexSection]:
    """Prepare resume body sections from data.

    This is a pure function that transforms resume data into structured
    LatexSection objects ready for template rendering.

    Args:
        data: Resume data dictionary with 'body' key containing sections.

    Returns:
        List of LatexSection objects.

    Examples:
        >>> data = {
        ...     "body": {
        ...         "Experience": [
        ...             {"title": "Software Engineer", "company": "Tech Corp"}
        ...         ]
        ...     }
        ... }
        >>> sections = prepare_sections(data)
        >>> len(sections)
        1

    """
    sections: list[LatexSection] = []
    body = data.get("body")
    if not isinstance(body, dict):
        return sections

    for section_name, entries in body.items():
        if not isinstance(entries, list):
            continue

        rendered_title = convert_inline(str(section_name))
        rendered_entries: list[LatexEntry] = []

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            title = linkify(entry.get("title"), entry.get("title_link"))
            subtitle = linkify(entry.get("company"), entry.get("company_link"))
            date_range = format_date(entry.get("start"), entry.get("end"))
            blocks = collect_blocks(entry.get("description"))

            rendered_entries.append(
                LatexEntry(
                    title=title or "",
                    subtitle=subtitle,
                    date_range=date_range,
                    blocks=blocks,
                )
            )

        if rendered_entries:
            sections.append(
                LatexSection(title=rendered_title, entries=rendered_entries)
            )

    return sections


def prepare_skill_sections(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Prepare skill sections from resume data.

    This is a pure function that transforms skill data into a list of
    skill group dictionaries ready for LaTeX rendering.

    Args:
        data: Resume data containing skill fields (expertise, programming, etc.).

    Returns:
        List of skill section dictionaries with title and items.

    Examples:
        >>> data = {"expertise": ["Python", "JavaScript"]}
        >>> sections = prepare_skill_sections(data)
        >>> sections[0]["title"]
        'Expertise'

    """
    titles = data.get("titles", {})
    skill_sections: list[dict[str, Any]] = []

    def append_groups(raw_value: Any, default_title: str) -> None:
        for group in format_skill_groups(raw_value):
            raw_items = group["items"]
            if not isinstance(raw_items, (list, tuple, set)):
                continue
            items = [convert_inline(str(item)) for item in raw_items if item]
            if not items:
                continue
            title = group["title"] or default_title
            skill_sections.append(
                {
                    "title": convert_inline(str(title)),
                    "items": items,
                }
            )

    append_groups(data.get("expertise"), titles.get("expertise", "Expertise"))
    append_groups(data.get("programming"), titles.get("programming", "Programming"))
    append_groups(data.get("keyskills"), titles.get("keyskills", "Key Skills"))
    append_groups(
        data.get("certification"), titles.get("certification", "Certifications")
    )

    return skill_sections


__all__ = [
    "build_contact_lines",
    "prepare_sections",
    "prepare_skill_sections",
]
