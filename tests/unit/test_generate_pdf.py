"""Unit tests for easyresume.generate_pdf module."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest
import yaml

from easyresume import config, rendering
from easyresume.generate_pdf import _open_file, generate_pdf, main
from tests.conftest import create_complete_cv_data


def _mock_render(
    name: str = "sample",
    preview: bool = False,
    paths: config.Paths | None = None,
) -> tuple[str, str, dict[str, object]]:
    context = {
        "cv_config": {
            "page_width": 190,
            "page_height": 270,
        }
    }
    return "<html></html>", "/base", context


class TestGeneratePdf:
    """Test cases for PDF generation functionality."""

    def _paths(self, tmp_path: Path) -> config.Paths:
        return config.Paths(
            data=tmp_path,
            input=tmp_path / "input",
            output=tmp_path / "output",
        )

    @patch("easyresume.generate_pdf.render_resume_html", side_effect=_mock_render)
    @patch("easyresume.generate_pdf.CSS")
    @patch("easyresume.generate_pdf.HTML")
    @patch("easyresume.generate_pdf.print")
    def test_generate_pdf_success_workflow(
        self,
        mock_print: Mock,
        mock_html: Mock,
        mock_css: Mock,
        mock_render: Mock,
        tmp_path: Path,
    ) -> None:
        """Verify standard PDF generation path."""
        paths = self._paths(tmp_path)
        paths.input.mkdir()
        paths.output.mkdir()

        (paths.input / "cv1.yaml").write_text(
            "template: a\nconfig: {}\n",
            encoding="utf-8",
        )
        (paths.input / "notes.txt").write_text("skip", encoding="utf-8")
        (paths.input / "cv2.yml").write_text(
            "template: b\nconfig: {}\n",
            encoding="utf-8",
        )

        html_instance = Mock()
        mock_html.return_value = html_instance
        css_instance = Mock()
        mock_css.return_value = css_instance

        generate_pdf(paths=paths)

        mock_render.assert_has_calls(
            [
                call("cv1", preview=False, paths=paths),
                call("cv2", preview=False, paths=paths),
            ],
            any_order=True,
        )
        assert mock_html.call_count == 2
        assert html_instance.write_pdf.call_count == 2
        assert mock_css.call_count == 2
        mock_print.assert_any_call(f"✓ Generated: {paths.output / 'cv1.pdf'}")

    @patch("easyresume.generate_pdf.render_resume_html", side_effect=_mock_render)
    @patch("easyresume.generate_pdf.CSS")
    @patch("easyresume.generate_pdf.HTML")
    @patch("easyresume.generate_pdf.print")
    def test_generate_pdf_creates_output_directory(
        self,
        mock_print: Mock,
        mock_html: Mock,
        mock_css: Mock,
        mock_render: Mock,
        tmp_path: Path,
    ) -> None:
        """Output directory is created when missing."""
        paths = self._paths(tmp_path)
        paths.input.mkdir()

        (paths.input / "cv1.yaml").write_text(
            "template: x\nconfig: {}\n",
            encoding="utf-8",
        )

        html_instance = Mock()
        mock_html.return_value = html_instance
        mock_css.return_value = Mock()

        assert not paths.output.exists()

        generate_pdf(paths=paths)

        assert paths.output.exists()

        html_instance.write_pdf.assert_called_once_with(
            str(paths.output / "cv1.pdf"), stylesheets=[mock_css.return_value]
        )

    def test_generate_pdf_filters_non_yaml_files(self, tmp_path: Path) -> None:
        """Fail when no YAML files are discovered."""
        paths = self._paths(tmp_path)
        paths.input.mkdir()
        paths.output.mkdir()
        (paths.input / "notes.txt").write_text("skip", encoding="utf-8")

        with pytest.raises(FileNotFoundError, match="No YAML files found"):
            generate_pdf(paths=paths)

    @patch(
        "easyresume.generate_pdf.render_resume_html",
        return_value=(
            "<html></html>",
            "/base",
            {"cv_config": {"page_width": 210, "page_height": 297}},
        ),
    )
    @patch("easyresume.generate_pdf.CSS")
    @patch("easyresume.generate_pdf.HTML")
    def test_generate_pdf_css_configuration(
        self,
        mock_html: Mock,
        mock_css: Mock,
        mock_render: Mock,
        tmp_path: Path,
    ) -> None:
        """Ensure CSS page size matches YAML config."""
        paths = self._paths(tmp_path)
        paths.input.mkdir()
        paths.output.mkdir()
        (paths.input / "test_cv.yaml").write_text(
            "template: x\nconfig: {}\n",
            encoding="utf-8",
        )

        html_instance = Mock()
        mock_html.return_value = html_instance
        css_instance = Mock()
        mock_css.return_value = css_instance

        generate_pdf(paths=paths)

        mock_css.assert_called_once_with(
            string="@page {size: 210mm 297mm; margin: 0mm;}"
        )
        html_instance.write_pdf.assert_called_once_with(
            str(paths.output / "test_cv.pdf"), stylesheets=[css_instance]
        )
        mock_html.assert_called_once_with(string="<html></html>", base_url="/base")

    @patch("easyresume.generate_pdf.render_resume_html", side_effect=_mock_render)
    @patch("easyresume.generate_pdf.CSS")
    @patch("easyresume.generate_pdf.HTML")
    @patch("easyresume.generate_pdf.print")
    def test_generate_pdf_with_mixed_extensions(
        self,
        mock_print: Mock,
        mock_html: Mock,
        mock_css: Mock,
        mock_render: Mock,
        tmp_path: Path,
    ) -> None:
        """Handle YAML/YML extensions regardless of case."""
        paths = self._paths(tmp_path)
        paths.input.mkdir()
        paths.output.mkdir()
        for filename in ["cv1.yaml", "cv2.yml", "cv3.YAML", "cv4.YML", "document.txt"]:
            (paths.input / filename).write_text(
                "template: x\nconfig: {}\n",
                encoding="utf-8",
            )

        html_instance = Mock()
        mock_html.return_value = html_instance
        mock_css.return_value = Mock()

        generate_pdf(paths=paths)

        assert mock_render.call_count == 4
        assert html_instance.write_pdf.call_count == 4

    @patch("easyresume.generate_pdf.render_resume_html", side_effect=_mock_render)
    def test_generate_pdf_empty_directory(
        self,
        mock_render: Mock,
        tmp_path: Path,
    ) -> None:
        """Raise when directory is empty."""
        paths = self._paths(tmp_path)
        paths.input.mkdir()
        paths.output.mkdir()

        with pytest.raises(FileNotFoundError, match="No YAML files found"):
            generate_pdf(paths=paths)


def _create_dataset(base_dir: Path, template_name: str, marker: str) -> config.Paths:
    """Create isolated content/input/output directories for PDF regression tests."""
    content_dir = base_dir / "package"
    templates_dir = content_dir / "templates"
    static_dir = content_dir / "static"
    templates_dir.mkdir(parents=True)
    static_dir.mkdir(parents=True)

    (templates_dir / f"{template_name}.html").write_text(
        f"<html><body><p>{marker}</p>{{{{ full_name }}}}</body></html>",
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


class _StubHTML:
    """Simplified stand-in for weasyprint.HTML for regression tests."""

    def __init__(self, *, string: str, base_url: str) -> None:
        self.string = string
        self.base_url = base_url

    def write_pdf(self, path: str, stylesheets: list[object]) -> None:  # noqa: D401
        Path(path).write_text(self.string, encoding="utf-8")


@patch("easyresume.generate_pdf.CSS", side_effect=lambda string: {"css": string})
@patch("easyresume.generate_pdf.HTML", side_effect=_StubHTML)
def test_generate_pdf_across_multiple_directories(
    mock_html: Mock,
    mock_css: Mock,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Regression: invoking generate_pdf twice respects per-call path configuration."""
    rendering.get_template_environment.cache_clear()
    base_one = tmp_path_factory.mktemp("pdf_dataset_one")
    base_two = tmp_path_factory.mktemp("pdf_dataset_two")

    paths_one = _create_dataset(base_one, "pdf_one", "PDF_ONE")
    paths_two = _create_dataset(base_two, "pdf_two", "PDF_TWO")

    generate_pdf(paths=paths_one)
    generate_pdf(paths=paths_two)

    pdf_one = (paths_one.output / "pdf_one.pdf").read_text(encoding="utf-8")
    pdf_two = (paths_two.output / "pdf_two.pdf").read_text(encoding="utf-8")

    assert "PDF_ONE" in pdf_one
    assert "PDF_TWO" not in pdf_one
    assert "PDF_TWO" in pdf_two
    assert "PDF_ONE" not in pdf_two

    assert mock_html.call_count == 2
    assert mock_css.call_count == 2

    @patch("easyresume.generate_pdf.render_resume_html", side_effect=_mock_render)
    @patch("easyresume.generate_pdf.CSS")
    @patch("easyresume.generate_pdf.HTML")
    @patch("easyresume.generate_pdf.print")
    def test_generate_pdf_error_handling(
        self,
        mock_print: Mock,
        mock_html: Mock,
        mock_css: Mock,
        mock_render: Mock,
        tmp_path: Path,
    ) -> None:
        """Errors from WeasyPrint are caught and reported."""
        paths = self._paths(tmp_path)
        paths.input.mkdir()
        paths.output.mkdir()
        (paths.input / "cv1.yaml").write_text(
            "template: x\nconfig: {}\n",
            encoding="utf-8",
        )

        html_instance = Mock()
        html_instance.write_pdf.side_effect = RuntimeError("render failed")
        mock_html.return_value = html_instance
        mock_css.return_value = Mock()

        generate_pdf(paths=paths)

        error_messages = [
            args[0]
            for args, _ in mock_print.call_args_list
            if (
                args
                and isinstance(args[0], str)
                and args[0].startswith("✗ Failed to generate")
            )
        ]
        assert error_messages

    @patch("easyresume.generate_pdf.render_resume_html", side_effect=_mock_render)
    @patch("easyresume.generate_pdf.CSS", return_value=Mock())
    @patch("easyresume.generate_pdf.HTML", return_value=Mock())
    @patch("easyresume.generate_pdf.print")
    @patch("easyresume.generate_pdf._open_file")
    def test_generate_pdf_open_flag(
        self,
        mock_open_file: Mock,
        mock_print: Mock,
        mock_html: Mock,
        mock_css: Mock,
        mock_render: Mock,
        tmp_path: Path,
    ) -> None:
        """Open viewer when open_after flag is set."""
        paths = self._paths(tmp_path)
        paths.input.mkdir()
        paths.output.mkdir()
        (paths.input / "cv1.yaml").write_text(
            "template: x\nconfig: {}\n",
            encoding="utf-8",
        )

        generate_pdf(open_after=True, paths=paths)
        mock_open_file.assert_called_once_with(str(paths.output / "cv1.pdf"))

    @patch("easyresume.generate_pdf.os.path.isdir", return_value=False)
    def test_generate_pdf_invalid_data_dir(self, mock_isdir: Mock) -> None:
        """Invalid data directory raises ValueError."""
        with pytest.raises(ValueError):
            generate_pdf(data_dir="does/not/exist")


class TestOpenFile:
    """Tests for the PDF viewer helper."""

    def test_open_file_linux(self, tmp_path: Path) -> None:
        """Open the Linux viewer when xdg-open is available."""
        temp_file = tmp_path / "output.pdf"

        with (
            patch("easyresume.generate_pdf.sys.platform", "linux"),
            patch("easyresume.generate_pdf.os.name", "posix"),
            patch(
                "easyresume.generate_pdf.shutil.which",
                return_value="/usr/bin/xdg-open",
            ),
            patch("easyresume.generate_pdf.subprocess.Popen") as mock_popen,
        ):
            _open_file(str(temp_file))

        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert args[0][0] == "/usr/bin/xdg-open"
        assert args[0][1] == str(temp_file)
        assert kwargs["stdout"] == subprocess.DEVNULL

    def test_open_file_error_logs_warning(self, tmp_path: Path) -> None:
        """Log a warning when launching the viewer fails."""
        failing_path = tmp_path / "missing.pdf"

        with (
            patch("easyresume.generate_pdf.sys.platform", "linux"),
            patch("easyresume.generate_pdf.os.name", "posix"),
            patch(
                "easyresume.generate_pdf.shutil.which",
                return_value="/usr/bin/xdg-open",
            ),
            patch(
                "easyresume.generate_pdf.subprocess.Popen",
                side_effect=FileNotFoundError("missing"),
            ),
            patch("easyresume.generate_pdf.sys.stderr") as mock_stderr,
        ):
            _open_file(str(failing_path))

        mock_stderr.write.assert_called()


class TestGeneratePdfMain:
    """Command-line interface behaviour."""

    @patch("easyresume.generate_pdf.generate_pdf")
    @patch("easyresume.generate_pdf.argparse.ArgumentParser.parse_args")
    def test_main_with_arguments(
        self, mock_parse_args: Mock, mock_generate: Mock
    ) -> None:
        """main() forwards CLI arguments."""
        mock_parse_args.return_value = Mock(data_dir="sample", open=True)

        main()

        mock_generate.assert_called_once_with(data_dir="sample", open_after=True)
