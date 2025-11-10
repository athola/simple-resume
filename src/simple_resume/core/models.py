"""Define core dataclasses for resume rendering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import Paths
from ..constants import OutputFormat, RenderMode


@dataclass(frozen=True)
class ResumeConfig:
    """Define a normalized resume configuration with validated fields."""

    page_width: int | None = None
    page_height: int | None = None
    sidebar_width: int | None = None
    output_mode: str = "markdown"
    template: str = "resume_no_bars"
    color_scheme: str = "default"

    # Color fields
    theme_color: str = "#0395DE"
    sidebar_color: str = "#F6F6F6"
    sidebar_text_color: str = "#000000"
    sidebar_bold_color: str = "#000000"
    bar_background_color: str = "#DFDFDF"
    date2_color: str = "#616161"
    frame_color: str = "#757575"
    heading_icon_color: str = "#0395DE"
    bold_color: str = "#585858"

    # Layout customization fields (section heading icons)
    section_icon_circle_size: str = "7.8mm"
    section_icon_circle_x_offset: str = "-0.5mm"
    section_icon_design_size: str = "4mm"
    section_icon_design_x_offset: str = "-0.1mm"
    section_icon_design_y_offset: str = "-0.4mm"
    section_heading_text_margin: str = "-6mm"


@dataclass(frozen=True)
class RenderPlan:
    """Define a pure data structure describing how to render a resume."""

    name: str
    mode: RenderMode
    config: ResumeConfig
    template_name: str | None = None
    context: dict[str, Any] | None = None
    tex: str | None = None
    palette_metadata: dict[str, Any] | None = None
    base_path: Path | str = ""


@dataclass(frozen=True)
class ValidationResult:
    """Define the result of validating resume data."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    normalized_config: ResumeConfig | None = None
    palette_metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class GenerationConfig:
    """Define a complete configuration for generation operations."""

    # Path configuration
    data_dir: str | Path | None = None
    output_dir: str | Path | None = None
    output_path: str | Path | None = None
    paths: Paths | None = None

    # Generation options
    template: str | None = None
    format: OutputFormat | str = OutputFormat.PDF
    open_after: bool = False
    preview: bool = False
    name: str | None = None
    pattern: str = "*"
    browser: str | None = None
    formats: list[OutputFormat | str] | None = None


__all__ = [
    "GenerationConfig",
    "RenderPlan",
    "ResumeConfig",
    "ValidationResult",
]
