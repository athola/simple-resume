"""Unit tests for HTML generation CLI."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from easyresume import config, rendering
from easyresume.generate_html import _inject_base_href, generate_html
from tests.conftest import create_complete_cv_data


def test_inject_base_href_adds_base_tag(tmp_path: Path) -> None:
    """Ensure a single <base> tag is injected into HTML output."""
    base = tmp_path
    html = "<html><head><title>Test</title></head><body></body></html>"
    result = _inject_base_href(html, base)
    assert '<base href="' in result
    assert result.count("<base") == 1


@patch("easyresume.generate_html.render_resume_html")
def test_generate_html_writes_files(render_resume_html: Mock, tmp_path: Path) -> None:
    """Write HTML files to disk with injected base path."""
    data_dir = tmp_path
    input_dir = data_dir / "input"
    output_dir = data_dir / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    (input_dir / "cv1.yaml").write_text(
        "template: cv_no_bars\nconfig: {}\n", encoding="utf-8"
    )

    render_resume_html.return_value = (
        "<html><head></head><body>Resume</body></html>",
        str(tmp_path / "src/easyresume"),
        {},
    )

    generate_html(data_dir=data_dir)

    output_file = output_dir / "cv1.html"
    assert output_file.exists()
    html = output_file.read_text(encoding="utf-8")
    assert "<base href=" in html
    render_resume_html.assert_called_once()
    args, kwargs = render_resume_html.call_args
    assert args[0] == "cv1"
    assert kwargs["preview"] is True
    assert "paths" in kwargs
    assert kwargs["paths"].input == input_dir


@patch("easyresume.generate_html.render_resume_html")
@patch("easyresume.generate_html.subprocess.Popen")
@patch("easyresume.generate_html.shutil.which")
def test_generate_html_open_browser(
    mock_which: Mock,
    mock_popen: Mock,
    render_resume_html: Mock,
    tmp_path: Path,
) -> None:
    """Launch configured browser when --open flag is set."""
    data_dir = tmp_path
    input_dir = data_dir / "input"
    output_dir = data_dir / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    (input_dir / "cv1.yaml").write_text(
        "template: cv_no_bars\nconfig: {}\n", encoding="utf-8"
    )

    mock_which.side_effect = lambda cmd: (
        "/usr/bin/firefox" if cmd == "firefox" else None
    )
    render_resume_html.return_value = (
        "<html><head></head><body>Resume</body></html>",
        str(tmp_path / "src/easyresume"),
        {},
    )

    generate_html(data_dir=data_dir, open_after=True)

    mock_popen.assert_called_once()
    args, _ = mock_popen.call_args
    assert args[0][0] == "firefox"


def test_generate_html_no_yaml(tmp_path: Path) -> None:
    """Raise when no YAML input files are present."""
    data_dir = tmp_path
    (data_dir / "input").mkdir()
    (data_dir / "output").mkdir()

    with pytest.raises(FileNotFoundError):
        generate_html(data_dir=data_dir)


def _create_dataset(base_dir: Path, template_name: str, marker: str) -> config.Paths:
    """Create isolated content/input/output directories for HTML generation tests."""
    content_dir = base_dir / "package"
    templates_dir = content_dir / "templates"
    static_dir = content_dir / "static"
    templates_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)

    template_file = templates_dir / f"{template_name}.html"
    template_file.write_text(
        f"<html><body><h1>{marker}</h1>{{{{ full_name }}}}</body></html>",
        encoding="utf-8",
    )

    data_dir = base_dir / "data"
    input_dir = data_dir / "input"
    output_dir = data_dir / "output"
    input_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)

    cv_data = create_complete_cv_data(
        template=template_name,
        full_name=f"{marker} User",
    )
    for key in ("page_width", "page_height", "sidebar_width"):
        cv_data["config"][key] = str(cv_data["config"][key])

    (input_dir / f"{template_name}.yaml").write_text(
        yaml.dump(cv_data), encoding="utf-8"
    )

    return config.Paths(
        data=data_dir,
        input=input_dir,
        output=output_dir,
        content=content_dir,
        templates=templates_dir,
        static=static_dir,
    )


def test_generate_html_across_multiple_directories(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Regression: invoking generate_html twice respects per-call path configuration."""
    rendering.get_template_environment.cache_clear()
    base_one = tmp_path_factory.mktemp("dataset_one")
    base_two = tmp_path_factory.mktemp("dataset_two")

    paths_one = _create_dataset(base_one, "custom_one", "DATASET_ONE")
    paths_two = _create_dataset(base_two, "custom_two", "DATASET_TWO")

    generate_html(paths=paths_one)
    generate_html(paths=paths_two)

    html_one = (paths_one.output / "custom_one.html").read_text(encoding="utf-8")
    html_two = (paths_two.output / "custom_two.html").read_text(encoding="utf-8")

    assert "DATASET_ONE" in html_one
    assert "DATASET_TWO" not in html_one
    assert "DATASET_TWO" in html_two
    assert "DATASET_ONE" not in html_two
