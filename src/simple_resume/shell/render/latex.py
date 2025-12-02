#!/usr/bin/env python3
"""Render resumes as LaTeX documents (shell layer with I/O operations)."""

from __future__ import annotations

import shutil

# Bandit: subprocess usage is confined to vetted TeX commands.
import subprocess  # nosec B404
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from simple_resume.core.latex import (
    LatexRenderResult,
    build_latex_context_pure,
    fontawesome_support_block,
)
from simple_resume.core.paths import Paths
from simple_resume.shell import config
from simple_resume.shell.runtime.content import get_content


class LatexCompilationError(RuntimeError):
    """Raise when LaTeX compilation fails."""

    def __init__(self, message: str, *, log: str | None = None) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            log: The compilation log.

        """
        super().__init__(message)
        self.log = log


def _jinja_environment(template_root: Path) -> Environment:
    """Return a Jinja2 environment for LaTeX templates.

    This is an I/O operation that loads templates from the file system.

    Args:
        template_root: Path to template directory.

    Returns:
        Configured Jinja2 environment.

    """
    loader = FileSystemLoader(str(template_root))
    env = Environment(loader=loader, autoescape=select_autoescape(("html", "xml")))
    return env


def build_latex_context(
    data: dict[str, Any],
    *,
    static_dir: Path | None = None,
) -> dict[str, Any]:
    """Prepare the LaTeX template context from raw resume data (with I/O).

    This shell function wraps the pure core function and adds file system
    operations for FontAwesome font detection.

    Args:
        data: Raw resume data dictionary.
        static_dir: Path to static assets directory for font detection.

    Returns:
        Dictionary of context variables for LaTeX template rendering.

    """
    # Get pure context from core
    context = build_latex_context_pure(data)

    # Add fontawesome_block with file system check (I/O operation)
    fontawesome_dir: str | None = None
    if static_dir is not None:
        candidate = Path(static_dir) / "fonts" / "fontawesome"
        if candidate.is_dir():  # I/O: file system check
            fontawesome_dir = f"{candidate.resolve().as_posix()}/"

    context["fontawesome_block"] = fontawesome_support_block(fontawesome_dir)

    return context


def render_resume_latex_from_data(
    data: dict[str, Any],
    *,
    paths: Paths | None = None,
    template_name: str = "latex/basic.tex",
) -> LatexRenderResult:
    """Render a LaTeX template with the prepared context.

    This function performs I/O operations: template loading and rendering.

    Args:
        data: Resume data dictionary.
        paths: Path configuration (resolved if not provided).
        template_name: Template file name to render.

    Returns:
        LatexRenderResult with rendered tex and context.

    """
    resolved_paths = paths or config.resolve_paths()
    context = build_latex_context(data, static_dir=resolved_paths.static)

    # I/O operations: load and render template
    env = _jinja_environment(resolved_paths.templates)
    template = env.get_template(template_name)
    tex = template.render(**context)

    return LatexRenderResult(tex=tex, context=context)


def render_resume_latex(
    name: str,
    *,
    paths: Paths | None = None,
    template_name: str = "latex/basic.tex",
) -> LatexRenderResult:
    """Read resume data and render it to a LaTeX string.

    This function performs I/O operations: reading resume data from file system.

    Args:
        name: Resume name to load.
        paths: Path configuration (resolved if not provided).
        template_name: Template file name to render.

    Returns:
        LatexRenderResult with rendered tex and context.

    """
    resolved_paths = paths or config.resolve_paths()

    # I/O operation: read resume data
    data = get_content(name, paths=resolved_paths, transform_markdown=False)

    return render_resume_latex_from_data(
        data, paths=resolved_paths, template_name=template_name
    )


def compile_tex_to_pdf(
    tex_path: Path,
    *,
    engines: Iterable[str] = ("xelatex", "pdflatex"),
) -> Path:
    """Compile a `.tex` file to PDF using an available LaTeX engine.

    This function performs I/O operations: subprocess execution and file system access.

    Args:
        tex_path: Path to .tex file to compile.
        engines: LaTeX engines to try (in order).

    Returns:
        Path to generated PDF file.

    Raises:
        LatexCompilationError: If compilation fails.

    """
    # I/O: Check which LaTeX engine is available
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

    # I/O: Execute subprocess
    # Bandit: command arguments are constructed from vetted engine names and paths.
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
    """Compile a `.tex` file to HTML using an available tool.

    This function performs I/O operations: subprocess execution and file system access.

    Args:
        tex_path: Path to .tex file to compile.
        tools: Conversion tools to try (in order).

    Returns:
        Path to generated HTML file.

    Raises:
        LatexCompilationError: If compilation fails.

    """
    html_path = tex_path.with_suffix(".html")
    tex_argument = str(tex_path) if tex_path.is_absolute() else tex_path.name

    last_error: LatexCompilationError | None = None

    # I/O: Try each tool
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

        # I/O: Execute subprocess
        # Bandit: conversion command uses whitelisted tool names and the
        # rendered tex path.
        result = subprocess.run(  # noqa: S603  # nosec B603
            command,
            cwd=str(tex_path.parent),
            capture_output=True,
            check=False,
        )

        if result.returncode == 0:
            # I/O: Check/rename generated file
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
    "build_latex_context",
    "compile_tex_to_html",
    "compile_tex_to_pdf",
    "render_resume_latex",
    "render_resume_latex_from_data",
]
