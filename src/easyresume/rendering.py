#!/usr/bin/env python3
"""Shared helpers for rendering CV templates without relying on Flask."""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import config
from .utilities import FILE_DEFAULT, get_content


def load_resume(
    name: str = "",
    *,
    preview: bool = True,
    paths: config.Paths | None = None,
) -> tuple[str, dict[str, Any]]:
    """Return the template name and render context for a CV."""
    resume_name = name or FILE_DEFAULT
    resolved_paths = paths or config.resolve_paths()
    data = get_content(resume_name, paths=resolved_paths)

    template_name = data.get("template", "cv_no_bars")

    context = dict(data)
    cv_config = context.pop("config", None)
    if cv_config is None:
        raise ValueError(
            f"Missing 'config' section in resume data for {resume_name}. "
            "Add a config block with page dimensions and colors."
        )

    context["cv_config"] = cv_config
    context["preview"] = preview

    return f"{template_name}.html", context


@cache
def get_template_environment(
    templates_dir: str | Path | None = None,
) -> Environment:
    """Create (once) and return the Jinja environment used for rendering."""
    template_root = Path(templates_dir or config.TEMPLATE_LOC)
    loader = FileSystemLoader(str(template_root))
    env = Environment(
        loader=loader,
        autoescape=select_autoescape(("html", "xml")),
    )

    def url_for(endpoint: str, *, filename: str = "") -> str:
        if endpoint != "static":
            raise ValueError(f"Unsupported endpoint '{endpoint}' in url_for()")
        if not filename:
            raise ValueError("url_for('static', filename=...) requires a filename")
        return f"static/{filename}"

    env.globals["url_for"] = url_for
    return env


def render_resume_html(
    name: str = "",
    *,
    preview: bool = False,
    paths: config.Paths | None = None,
) -> tuple[str, str, dict[str, Any]]:
    """Render a resume to HTML string and return it with base path and context."""
    resolved_paths = paths or config.resolve_paths()
    template_name, context = load_resume(name, preview=preview, paths=resolved_paths)
    env = get_template_environment(str(resolved_paths.templates))
    template = env.get_template(template_name)
    html = template.render(**context)

    base_path = resolved_paths.content
    return html, str(base_path), context
