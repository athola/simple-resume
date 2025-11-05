#!/usr/bin/env python3
"""Render resumes as LaTeX documents."""

from __future__ import annotations

import itertools
import re
import shutil
import subprocess  # nosec B404
import textwrap
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypedDict

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import config
from .utilities import format_skill_groups, get_content

LATEX_SPECIAL_CHARS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex(text: str) -> str:
    """Escape LaTeX special characters in text."""
    return "".join(LATEX_SPECIAL_CHARS.get(char, char) for char in text)


def escape_url(url: str) -> str:
    """Escape characters that break LaTeX hyperlink URLs."""
    replacements = {"%": r"\%", "#": r"\#", "&": r"\&", "_": r"\_"}
    return "".join(replacements.get(char, char) for char in url)


class ParagraphBlock(TypedDict):
    """Paragraph text block."""

    kind: Literal["paragraph"]
    text: str


class ListBlock(TypedDict):
    """Bullet or enumerated list block."""

    kind: Literal["itemize", "enumerate"]
    items: list[str]


Block = ParagraphBlock | ListBlock


@dataclass(frozen=True)
class LatexEntry:
    """Single entry inside a resume section."""

    title: str
    subtitle: str | None
    date_range: str | None
    blocks: list[Block]


@dataclass(frozen=True)
class LatexSection:
    """Top-level resume section (Experience, Education, etc.)."""

    title: str
    entries: list[LatexEntry]


@dataclass(frozen=True)
class LatexRenderResult:
    """Rendered LaTeX output plus context for debugging or tests."""

    tex: str
    context: dict[str, Any]


def _jinja_environment(template_root: Path) -> Environment:
    loader = FileSystemLoader(str(template_root))
    env = Environment(loader=loader, autoescape=select_autoescape(("html", "xml")))
    return env


class _InlineConverter:
    """Convert limited Markdown inline formatting to LaTeX."""

    def __init__(self) -> None:
        self._placeholders: dict[str, str] = {}
        self._counter = itertools.count()

    def convert(self, text: str) -> str:
        """Return LaTeX-safe string."""
        working = text
        working = re.sub(r"`([^`]+)`", self._code_replacement, working)
        working = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            self._link_replacement,
            working,
        )
        working = re.sub(r"\*\*(.+?)\*\*", self._bold_replacement, working)
        working = re.sub(r"__(.+?)__", self._bold_replacement, working)
        working = re.sub(
            r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",
            self._italic_replacement,
            working,
        )
        working = re.sub(r"_(.+?)_", self._italic_replacement, working)

        escaped = escape_latex(working)
        for key, value in self._placeholders.items():
            escaped = escaped.replace(key, value)
        return escaped

    def _placeholder(self, value: str) -> str:
        token = f"LATEXPH{next(self._counter)}"
        self._placeholders[token] = value
        return token

    def _code_replacement(self, match: re.Match[str]) -> str:
        content = escape_latex(match.group(1))
        return self._placeholder(rf"\texttt{{{content}}}")

    def _link_replacement(self, match: re.Match[str]) -> str:
        label = _convert_inline(match.group(1))
        url = escape_url(match.group(2))
        return self._placeholder(rf"\href{{{url}}}{{{label}}}")

    def _bold_replacement(self, match: re.Match[str]) -> str:
        content = _convert_inline(match.group(1))
        return self._placeholder(rf"\textbf{{{content}}}")

    def _italic_replacement(self, match: re.Match[str]) -> str:
        content = _convert_inline(match.group(1))
        return self._placeholder(rf"\textit{{{content}}}")


def _convert_inline(text: str) -> str:
    """Convert simple Markdown inline formatting to LaTeX."""
    converter = _InlineConverter()
    return converter.convert(text)


def _normalize_iterable(value: Any) -> list[str]:
    """Return list of string entries regardless of input type."""
    if value is None:
        return []
    if isinstance(value, dict):
        items = []
        for key, val in value.items():
            item = f"{key} ({val})"
            items.append(_convert_inline(str(item)))
        return items
    if isinstance(value, (list, tuple, set)):
        return [_convert_inline(str(item)) for item in value]
    return [_convert_inline(str(value))]


def _collect_blocks(description: str | None) -> list[Block]:
    if not description:
        return []

    lines = description.strip("\n").splitlines()
    blocks: list[Block] = []
    current_items: list[str] = []
    ordered = False

    def flush_items() -> None:
        nonlocal current_items, ordered
        if current_items:
            converted = [_convert_inline(item) for item in current_items]
            kind: Literal["itemize", "enumerate"] = (
                "enumerate" if ordered else "itemize"
            )
            blocks.append({"kind": kind, "items": converted})
            current_items = []
            ordered = False

    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            flush_items()
            continue

        bullet_match = re.match(r"^[-*+]\s+(.*)", stripped)
        ordered_match = re.match(r"^\d+\.\s+(.*)", stripped)

        if bullet_match:
            if current_items and ordered:
                flush_items()
            ordered = False
            current_items.append(bullet_match.group(1).strip())
            continue

        if ordered_match:
            if current_items and not ordered:
                flush_items()
            ordered = True
            current_items.append(ordered_match.group(1).strip())
            continue

        if stripped.startswith(" ") and current_items:
            current_items[-1] = f"{current_items[-1]} {stripped.strip()}"
            continue

        flush_items()
        paragraph_text = _convert_inline(stripped)
        blocks.append({"kind": "paragraph", "text": paragraph_text})

    flush_items()
    return blocks


def _format_date(start: str | None, end: str | None) -> str | None:
    start_clean = start.strip() if isinstance(start, str) else ""
    end_clean = end.strip() if isinstance(end, str) else ""
    if start_clean and end_clean:
        if start_clean == end_clean:
            return _convert_inline(start_clean)
        return _convert_inline(f"{start_clean} -- {end_clean}")
    if end_clean:
        return _convert_inline(end_clean)
    if start_clean:
        return _convert_inline(start_clean)
    return None


def _linkify(text: str | None, link: str | None) -> str | None:
    if not text:
        return None
    rendered = _convert_inline(text)
    if link:
        return rf"\href{{{escape_url(link)}}}{{{rendered}}}"
    return rendered


def _build_contact_lines(data: dict[str, Any]) -> list[str]:
    lines: list[str] = []

    def _icon_prefix(icon: str) -> str:
        return rf"\{icon}\enspace "

    address = data.get("address")
    if isinstance(address, Iterable) and not isinstance(address, (str, bytes)):
        joined = ", ".join(str(part) for part in address if part)
    elif address:
        joined = str(address)
    else:
        joined = ""

    if joined:
        lines.append(f"{_icon_prefix('faLocation')}{_convert_inline(joined)}")

    phone = data.get("phone")
    if phone:
        lines.append(f"{_icon_prefix('faPhone')}{escape_latex(str(phone))}")

    email = data.get("email")
    if email:
        lines.append(
            rf"{_icon_prefix('faEnvelope')}\href{{mailto:{escape_url(email)}}}{{\nolinkurl{{{escape_latex(email)}}}}}"
        )

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

    web = data.get("web")
    if web:
        web_value = str(web)
        icon = "faGithub" if "github.com" in web_value.lower() else "faGlobe"
        if icon == "faGithub" and github_added:
            pass
        else:
            lines.append(
                rf"{_icon_prefix(icon)}\href{{{escape_url(web_value)}}}{{\nolinkurl{{{escape_latex(web_value)}}}}}"
            )

    linkedin = data.get("linkedin")
    if linkedin:
        url = linkedin
        if not url.startswith("http"):
            url = f"https://www.linkedin.com/{linkedin.lstrip('/')}"
        lines.append(
            rf"{_icon_prefix('faLinkedin')}\href{{{escape_url(url)}}}{{\nolinkurl{{{escape_latex(linkedin)}}}}}"
        )

    return lines


def _prepare_sections(data: dict[str, Any]) -> list[LatexSection]:
    sections: list[LatexSection] = []
    body = data.get("body")
    if not isinstance(body, dict):
        return sections

    for section_name, entries in body.items():
        if not isinstance(entries, list):
            continue

        rendered_title = _convert_inline(str(section_name))
        rendered_entries: list[LatexEntry] = []

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            title = _linkify(entry.get("title"), entry.get("title_link"))
            subtitle = _linkify(entry.get("company"), entry.get("company_link"))
            date_range = _format_date(entry.get("start"), entry.get("end"))
            blocks = _collect_blocks(entry.get("description"))

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


def _prepare_skill_sections(data: dict[str, Any]) -> list[dict[str, Any]]:
    titles = data.get("titles", {})
    skill_sections: list[dict[str, Any]] = []

    def append_groups(raw_value: Any, default_title: str) -> None:
        for group in format_skill_groups(raw_value):
            raw_items = group["items"]
            if not isinstance(raw_items, (list, tuple, set)):
                continue
            items = [_convert_inline(str(item)) for item in raw_items if item]
            if not items:
                continue
            title = group["title"] or default_title
            skill_sections.append(
                {
                    "title": _convert_inline(str(title)),
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


def build_latex_context(
    data: dict[str, Any],
    *,
    static_dir: Path | None = None,
) -> dict[str, Any]:
    """Prepare LaTeX template context from raw resume data."""
    full_name = _convert_inline(str(data.get("full_name", "")))
    headline = data.get("job_title")
    rendered_headline = _convert_inline(str(headline)) if headline else None
    summary_blocks = _collect_blocks(data.get("description"))
    fontawesome_dir: str | None = None
    if static_dir is not None:
        candidate = Path(static_dir) / "fonts" / "fontawesome"
        if candidate.is_dir():
            fontawesome_dir = f"{candidate.resolve().as_posix()}/"

    fontawesome_block = _fontawesome_support_block(fontawesome_dir)

    return {
        "full_name": full_name,
        "headline": rendered_headline,
        "contact_lines": _build_contact_lines(data),
        "summary_blocks": summary_blocks,
        "skill_sections": _prepare_skill_sections(data),
        "sections": _prepare_sections(data),
        "fontawesome_block": fontawesome_block,
    }


def _fontawesome_support_block(fontawesome_dir: str | None) -> str:
    """Return LaTeX block that defines contact icons."""
    fallback = textwrap.dedent(
        r"""
        \IfFileExists{fontawesome.sty}{%
          \usepackage{fontawesome}%
          \providecommand{\faLocation}{\faMapMarker}%
        }{
          \newcommand{\faPhone}{\textbf{P}}
          \newcommand{\faEnvelope}{\textbf{@}}
          \newcommand{\faLinkedin}{\textbf{in}}
          \newcommand{\faGlobe}{\textbf{W}}
          \newcommand{\faGithub}{\textbf{GH}}
          \newcommand{\faLocation}{\textbf{A}}
        }
        """
    ).strip()

    if not fontawesome_dir:
        return fallback

    fontspec_block = textwrap.dedent(
        rf"""
        \usepackage{{fontspec}}
        \newfontfamily\FAFreeSolid[
            Path={fontawesome_dir},
            Scale=0.72,
        ]{{Font Awesome 6 Free-Solid-900.otf}}
        \newfontfamily\FAFreeBrands[
            Path={fontawesome_dir},
            Scale=0.72,
        ]{{Font Awesome 6 Brands-Regular-400.otf}}
        \newcommand{{\faPhone}}{{%
          {{\FAFreeSolid\symbol{{"F095}}}}%
        }}
        \newcommand{{\faEnvelope}}{{%
          {{\FAFreeSolid\symbol{{"F0E0}}}}%
        }}
        \newcommand{{\faLinkedin}}{{%
          {{\FAFreeBrands\symbol{{"F08C}}}}%
        }}
        \newcommand{{\faGlobe}}{{%
          {{\FAFreeSolid\symbol{{"F0AC}}}}%
        }}
        \newcommand{{\faGithub}}{{%
          {{\FAFreeBrands\symbol{{"F09B}}}}%
        }}
        \newcommand{{\faLocation}}{{%
          {{\FAFreeSolid\symbol{{"F3C5}}}}%
        }}
        """
    ).strip()

    lines: list[str] = [r"\usepackage{iftex}", r"\ifPDFTeX"]
    fallback_lines = fallback.splitlines()
    lines.extend(f"  {line}" if line else "" for line in fallback_lines)
    lines.append(r"\else")
    fontspec_lines = fontspec_block.splitlines()
    lines.extend(f"  {line}" if line else "" for line in fontspec_lines)
    lines.append(r"\fi")
    return "\n".join(lines)


def render_resume_latex_from_data(
    data: dict[str, Any],
    *,
    paths: config.Paths | None = None,
    template_name: str = "latex/basic.tex",
) -> LatexRenderResult:
    """Render LaTeX template with prepared context."""
    resolved_paths = paths or config.resolve_paths()
    context = build_latex_context(data, static_dir=resolved_paths.static)
    env = _jinja_environment(resolved_paths.templates)
    template = env.get_template(template_name)
    tex = template.render(**context)
    return LatexRenderResult(tex=tex, context=context)


def render_resume_latex(
    name: str,
    *,
    paths: config.Paths | None = None,
    template_name: str = "latex/basic.tex",
) -> LatexRenderResult:
    """Read resume data and render to LaTeX string."""
    resolved_paths = paths or config.resolve_paths()
    data = get_content(name, paths=resolved_paths, transform_markdown=False)
    return render_resume_latex_from_data(
        data, paths=resolved_paths, template_name=template_name
    )


class LatexCompilationError(RuntimeError):
    """Raised when LaTeX compilation fails."""

    def __init__(self, message: str, *, log: str | None = None) -> None:
        """Initialize LaTeX compilation error with message and optional log."""
        super().__init__(message)
        self.log = log


def compile_tex_to_pdf(
    tex_path: Path,
    *,
    engines: Iterable[str] = ("xelatex", "pdflatex"),
) -> Path:
    """Compile a .tex file to PDF using an available LaTeX engine."""
    available_engine = None
    for engine in engines:
        if shutil.which(engine):
            available_engine = engine
            break

    if available_engine is None:
        raise LatexCompilationError(
            "No LaTeX engine found. Install xelatex or pdflatex to render PDFs."
        )

    tex_argument = str(tex_path) if tex_path.is_absolute() else tex_path.name

    command = [
        available_engine,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-output-directory",
        str(tex_path.parent.resolve()),
        tex_argument,
    ]

    result = subprocess.run(  # noqa: S603  # nosec B603
        command,
        cwd=str(tex_path.parent),
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        log = (result.stdout or b"") + b"\n" + (result.stderr or b"")
        message = f"LaTeX compilation failed with exit code {result.returncode}"
        raise LatexCompilationError(
            message,
            log=log.decode("utf-8", errors="ignore"),
        )

    pdf_path = tex_path.with_suffix(".pdf")
    return pdf_path


def compile_tex_to_html(
    tex_path: Path,
    *,
    tools: Iterable[str] = ("pandoc", "htlatex"),
) -> Path:
    """Compile a .tex file to HTML using available tooling.

    Preference order:
        1. pandoc (fast, single-shot)
        2. htlatex (requires TeX4ht distribution)

    Raises:
        LatexCompilationError: When no tools are available or compilation fails.

    """
    html_path = tex_path.with_suffix(".html")
    tex_argument = str(tex_path) if tex_path.is_absolute() else tex_path.name

    last_error: LatexCompilationError | None = None
    for tool in tools:
        if shutil.which(tool) is None:
            continue

        if tool == "pandoc":
            command = [
                tool,
                tex_argument,
                "-f",
                "latex",
                "-t",
                "html5",
                "-s",
                "-o",
                str(html_path),
            ]
        elif tool == "htlatex":
            command = [
                tool,
                tex_argument,
                "html",
            ]
        else:
            continue

        result = subprocess.run(  # noqa: S603  # nosec B603
            command,
            cwd=str(tex_path.parent),
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            if tool == "htlatex":
                generated = tex_path.with_suffix(".html")
                if generated.exists():
                    generated.rename(html_path)
            if not html_path.exists():
                html_path.write_text("", encoding="utf-8")
            return html_path

        log = (result.stdout or b"") + b"\n" + (result.stderr or b"")
        last_error = LatexCompilationError(
            f"LaTeX to HTML conversion via {tool} "
            f"failed with exit code {result.returncode}",
            log=log.decode("utf-8", errors="ignore"),
        )
        continue

    if last_error is not None:
        raise last_error
    raise LatexCompilationError(
        "No LaTeX-to-HTML tool found. Install pandoc or htlatex to render HTML output."
    )


__all__ = [
    "LatexCompilationError",
    "LatexRenderResult",
    "compile_tex_to_pdf",
    "compile_tex_to_html",
    "render_resume_latex",
    "render_resume_latex_from_data",
    "build_latex_context",
]
