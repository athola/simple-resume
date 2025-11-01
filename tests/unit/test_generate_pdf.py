"""Unit tests for easyresume.generate_pdf module."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
import yaml

from easyresume import config, rendering
from easyresume.generate_pdf import (
    LocalFileSystem,
    PageSpec,
    PdfGenerationDeps,
    PdfLogger,
    PdfWriter,
    _open_file,
    generate_pdf,
    main,
)
from tests.conftest import create_complete_resume_data


class StubRenderer:
    """Record renderer invocations and return canned responses."""

    def __init__(self, *, resume_config: dict[str, Any] | None = None) -> None:
        """Store render calls and optional resume configuration overrides."""
        self.calls: list[tuple[str, bool, config.Paths | None]] = []
        self.resume_config = resume_config or {"page_width": 190, "page_height": 270}

    def __call__(
        self, name: str, *, preview: bool, paths: config.Paths | None
    ) -> tuple[str, str, dict[str, Any]]:
        """Return deterministic HTML payload with default resume config."""
        self.calls.append((name, preview, paths))
        return "<html></html>", "/base", {"resume_config": dict(self.resume_config)}


class RecordingWriter(PdfWriter):
    """PdfWriter that stores each write call for assertions."""

    def __init__(self) -> None:
        """Initialize empty call log."""
        self.calls: list[dict[str, Any]] = []

    def write(
        self,
        *,
        output_path: Path,
        html: str,
        base_url: str,
        page: PageSpec,
    ) -> None:
        """Record each invocation for later verification."""
        self.calls.append(
            {
                "output_path": output_path,
                "html": html,
                "base_url": base_url,
                "page": page,
            }
        )


class RecordingLogger(PdfLogger):
    """Logger that records lifecycle events rather than printing."""

    def __init__(self) -> None:
        """Initialize tracking containers."""
        self.started: list[tuple[str, Path]] = []
        self.succeeded_events: list[tuple[str, Path]] = []
        self.failed_events: list[tuple[str, Path, Exception]] = []

    def starting(self, name: str, output_path: Path) -> None:
        """Track resume generation start."""
        self.started.append((name, output_path))

    def succeeded(self, name: str, output_path: Path) -> None:
        """Track completed resume generation."""
        self.succeeded_events.append((name, output_path))

    def failed(self, name: str, output_path: Path, error: Exception) -> None:
        """Track failed resume generation attempts."""
        self.failed_events.append((name, output_path, error))


class RecordingViewer:
    """Viewer stub that captures requested paths."""

    def __init__(self) -> None:
        """Initialize list to store requested file paths."""
        self.paths: list[str] = []

    def __call__(self, path: str) -> None:
        """Record a path that would have been opened."""
        self.paths.append(path)


class TestGeneratePdf:
    """Test cases for PDF generation functionality."""

    def _paths(self, tmp_path: Path) -> config.Paths:
        return config.Paths(
            data=tmp_path,
            input=tmp_path / "input",
            output=tmp_path / "output",
        )

    def _deps(
        self,
        *,
        resume_config: dict[str, Any] | None = None,
    ) -> tuple[
        StubRenderer,
        RecordingWriter,
        RecordingLogger,
        RecordingViewer,
        PdfGenerationDeps,
    ]:
        renderer = StubRenderer(resume_config=resume_config)
        writer = RecordingWriter()
        logger = RecordingLogger()
        viewer = RecordingViewer()
        deps = PdfGenerationDeps(
            renderer=renderer,
            writer=writer,
            logger=logger,
            viewer=viewer,
        )
        return renderer, writer, logger, viewer, deps

    def test_generate_pdf_success_workflow(self, tmp_path: Path) -> None:
        """Verify standard PDF generation path."""
        paths = self._paths(tmp_path)
        paths.input.mkdir()
        paths.output.mkdir()

        (paths.input / "resume1.yaml").write_text(
            "template: a\nconfig: {}\n", encoding="utf-8"
        )
        (paths.input / "notes.txt").write_text("skip", encoding="utf-8")
        (paths.input / "resume2.yml").write_text(
            "template: b\nconfig: {}\n", encoding="utf-8"
        )

        renderer, writer, logger, viewer, deps = self._deps()

        generate_pdf(
            paths=paths,
            deps=deps,
            filesystem=LocalFileSystem(),
        )

        assert {call[0] for call in renderer.calls} == {"resume1", "resume2"}
        assert all(preview is False for _, preview, _ in renderer.calls)
        assert len(writer.calls) == 2
        assert {entry["output_path"].name for entry in writer.calls} == {
            "resume1.pdf",
            "resume2.pdf",
        }
        assert {event[0] for event in logger.succeeded_events} == {"resume1", "resume2"}
        assert not logger.failed_events
        assert viewer.paths == []

    def test_generate_pdf_creates_output_directory(self, tmp_path: Path) -> None:
        """Output directory is created when missing."""
        paths = self._paths(tmp_path)
        paths.input.mkdir()

        (paths.input / "resume1.yaml").write_text(
            "template: x\nconfig: {}\n", encoding="utf-8"
        )

        renderer, writer, logger, viewer, deps = self._deps()

        assert not paths.output.exists()

        generate_pdf(
            paths=paths,
            deps=deps,
            filesystem=LocalFileSystem(),
        )

        assert paths.output.exists()
        assert len(writer.calls) == 1

    def test_generate_pdf_filters_non_yaml_files(self, tmp_path: Path) -> None:
        """Fail when no YAML files are discovered."""
        paths = self._paths(tmp_path)
        paths.input.mkdir()
        paths.output.mkdir()
        (paths.input / "notes.txt").write_text("skip", encoding="utf-8")

        renderer, writer, logger, viewer, deps = self._deps()

        with pytest.raises(FileNotFoundError, match="No YAML files found"):
            generate_pdf(
                paths=paths,
                deps=deps,
                filesystem=LocalFileSystem(),
            )

        assert renderer.calls == []
        assert writer.calls == []

    def test_generate_pdf_css_configuration(
        self,
        tmp_path: Path,
    ) -> None:
        """Ensure CSS page size matches YAML config."""
        paths = self._paths(tmp_path)
        paths.input.mkdir()
        paths.output.mkdir()
        (paths.input / "test_resume.yaml").write_text(
            "template: x\nconfig: {}\n",
            encoding="utf-8",
        )

        renderer = StubRenderer(
            resume_config={"page_width": "210", "page_height": "297"}
        )
        writer = RecordingWriter()
        logger = RecordingLogger()
        viewer = RecordingViewer()
        deps = PdfGenerationDeps(
            renderer=renderer,
            writer=writer,
            logger=logger,
            viewer=viewer,
        )

        generate_pdf(paths=paths, deps=deps, filesystem=LocalFileSystem())

        assert len(writer.calls) == 1
        page_spec = writer.calls[0]["page"]
        assert page_spec.width_mm == 210
        assert page_spec.height_mm == 297

    def test_generate_pdf_with_mixed_extensions(
        self,
        tmp_path: Path,
    ) -> None:
        """Handle YAML/YML extensions regardless of case."""
        paths = self._paths(tmp_path)
        paths.input.mkdir()
        paths.output.mkdir()
        for filename in [
            "resume1.yaml",
            "resume2.yml",
            "resume3.YAML",
            "resume4.YML",
            "document.txt",
        ]:
            (paths.input / filename).write_text(
                "template: x\nconfig: {}\n",
                encoding="utf-8",
            )

        renderer, writer, logger, viewer, deps = self._deps()

        generate_pdf(paths=paths, deps=deps, filesystem=LocalFileSystem())

        assert len(writer.calls) == 4
        assert {entry["output_path"].name for entry in writer.calls} == {
            "resume1.pdf",
            "resume2.pdf",
            "resume3.pdf",
            "resume4.pdf",
        }

    def test_generate_pdf_empty_directory(self, tmp_path: Path) -> None:
        """Raise when directory is empty."""
        paths = self._paths(tmp_path)
        paths.input.mkdir()
        paths.output.mkdir()

        renderer, writer, logger, viewer, deps = self._deps()

        with pytest.raises(FileNotFoundError, match="No YAML files found"):
            generate_pdf(
                paths=paths,
                deps=deps,
                filesystem=LocalFileSystem(),
            )


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

    resume_data = create_complete_resume_data(
        template=template_name,
        full_name=f"{marker} User",
    )
    for key in ("page_width", "page_height", "sidebar_width"):
        resume_data["config"][key] = str(resume_data["config"][key])

    (input_dir / f"{template_name}.yaml").write_text(
        yaml.dump(resume_data), encoding="utf-8"
    )

    return config.Paths(
        data=data_dir,
        input=input_dir,
        output=output_dir,
        content=content_dir,
        templates=templates_dir,
        static=static_dir,
    )


class _FileWritingWriter(PdfWriter):
    """PdfWriter that writes HTML payloads to disk for regression checks."""

    def write(
        self,
        *,
        output_path: Path,
        html: str,
        base_url: str,
        page: PageSpec,
    ) -> None:
        output_path.write_text(html, encoding="utf-8")


def test_generate_pdf_across_multiple_directories(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Regression: invoking generate_pdf twice respects per-call path configuration."""
    rendering.get_template_environment.cache_clear()
    base_one = tmp_path_factory.mktemp("pdf_dataset_one")
    base_two = tmp_path_factory.mktemp("pdf_dataset_two")

    paths_one = _create_dataset(base_one, "pdf_one", "PDF_ONE")
    paths_two = _create_dataset(base_two, "pdf_two", "PDF_TWO")

    writer = _FileWritingWriter()
    logger = RecordingLogger()
    viewer = RecordingViewer()
    deps = PdfGenerationDeps(
        renderer=rendering.render_resume_html,
        writer=writer,
        logger=logger,
        viewer=viewer,
    )
    fs = LocalFileSystem()

    generate_pdf(paths=paths_one, deps=deps, filesystem=fs)
    generate_pdf(paths=paths_two, deps=deps, filesystem=fs)

    pdf_one = (paths_one.output / "pdf_one.pdf").read_text(encoding="utf-8")
    pdf_two = (paths_two.output / "pdf_two.pdf").read_text(encoding="utf-8")

    assert "PDF_ONE" in pdf_one
    assert "PDF_TWO" not in pdf_one
    assert "PDF_TWO" in pdf_two
    assert "PDF_ONE" not in pdf_two


def test_generate_pdf_error_handling(tmp_path: Path) -> None:
    """Errors from the writer are caught and reported."""
    paths = config.Paths(
        data=tmp_path,
        input=tmp_path / "input",
        output=tmp_path / "output",
    )
    paths.input.mkdir()
    paths.output.mkdir()
    (paths.input / "resume1.yaml").write_text(
        "template: x\nconfig: {}\n", encoding="utf-8"
    )

    renderer = StubRenderer()
    logger = RecordingLogger()
    viewer = RecordingViewer()

    class FailingWriter(PdfWriter):
        def write(
            self,
            *,
            output_path: Path,
            html: str,
            base_url: str,
            page: PageSpec,
        ) -> None:
            raise RuntimeError("render failed")

    deps = PdfGenerationDeps(
        renderer=renderer,
        writer=FailingWriter(),
        logger=logger,
        viewer=viewer,
    )

    generate_pdf(paths=paths, deps=deps, filesystem=LocalFileSystem())

    assert len(logger.failed_events) == 1
    failure = logger.failed_events[0]
    assert failure[0] == "resume1"
    assert isinstance(failure[2], RuntimeError)


def test_generate_pdf_open_flag(tmp_path: Path) -> None:
    """Open viewer when open_after flag is set."""
    paths = config.Paths(
        data=tmp_path,
        input=tmp_path / "input",
        output=tmp_path / "output",
    )
    paths.input.mkdir()
    paths.output.mkdir()
    (paths.input / "resume1.yaml").write_text(
        "template: x\nconfig: {}\n", encoding="utf-8"
    )

    renderer = StubRenderer()
    writer = RecordingWriter()
    logger = RecordingLogger()
    viewer = RecordingViewer()
    deps = PdfGenerationDeps(
        renderer=renderer,
        writer=writer,
        logger=logger,
        viewer=viewer,
    )

    generate_pdf(open_after=True, paths=paths, deps=deps, filesystem=LocalFileSystem())

    assert viewer.paths == [str(paths.output / "resume1.pdf")]


def test_generate_pdf_invalid_data_dir() -> None:
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
