"""Unit tests for shell generation orchestration with I/O dependencies.

These tests use dependency injection to test the imperative shell layer without
actually performing file I/O or external subprocess calls.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from simple_resume import config
from simple_resume.core.resume import RenderPlan, ResumeConfig
from simple_resume.latex_renderer import LatexCompilationError
from simple_resume.shell.generation import (
    GenerationDeps,
    HtmlWriter,
    LocalFileSystem,
    PageSpec,
    PrintLogger,
    ResumeGenerator,
    WeasyPrintWriter,
)


class MockFileSystem:
    """Mock filesystem for testing."""

    def __init__(
        self, directories: set[Path] = None, files: dict[Path, str] = None
    ) -> None:
        self.directories = directories or set()
        self.files = files or {}

    def ensure_dir(self, path: Path) -> None:
        self.directories.add(path)

    def iterdir(self, path: Path) -> list[Path]:
        return [p for p in self.files.keys() if p.parent == path]

    def is_dir(self, path: Path) -> bool:
        return path in self.directories


class MockPdfWriter:
    """Mock PDF writer for testing."""

    def __init__(self) -> None:
        self.writes: list[dict[str, Any]] = []

    def write(
        self, *, output_path: Path, html: str, base_url: str, page: PageSpec
    ) -> None:
        self.writes.append(
            {
                "output_path": output_path,
                "html": html,
                "base_url": base_url,
                "page": page,
            }
        )


class MockHtmlWriter:
    """Mock HTML writer for testing."""

    def __init__(self) -> None:
        self.writes: list[dict[str, Any]] = []

    def write(self, *, output_path: Path, html: str) -> None:
        self.writes.append(
            {
                "output_path": output_path,
                "html": html,
            }
        )


class MockLogger:
    """Mock logger for testing."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def starting(self, name: str, output_path: Path) -> None:
        self.events.append(
            {"type": "starting", "name": name, "output_path": output_path}
        )

    def succeeded(self, name: str, output_path: Path) -> None:
        self.events.append(
            {"type": "succeeded", "name": name, "output_path": output_path}
        )

    def failed(self, name: str, output_path: Path, error: Exception) -> None:
        self.events.append(
            {"type": "failed", "name": name, "output_path": output_path, "error": error}
        )


class MockViewer:
    """Mock file viewer for testing."""

    def __init__(self) -> None:
        self.opened_files: list[str] = []

    def __call__(self, path: str) -> None:
        self.opened_files.append(path)


class TestResumeGenerator:
    """Test ResumeGenerator with mocked dependencies."""

    @pytest.fixture
    def mock_deps(self) -> GenerationDeps:
        """Create mock dependencies for testing."""
        return GenerationDeps(
            pdf_writer=MockPdfWriter(),
            html_writer=MockHtmlWriter(),
            logger=MockLogger(),
            viewer=MockViewer(),
            filesystem=MockFileSystem(),
        )

    @pytest.fixture
    def sample_paths(self) -> config.Paths:
        """Create sample paths for testing."""
        return config.Paths(
            data=Path("/data"),
            input=Path("/data/input"),
            output=Path("/data/output"),
            content=Path("/content"),
            templates=Path("/content/templates"),
            static=Path("/content/static"),
        )

    @pytest.fixture
    def sample_yaml_files(self) -> dict[Path, str]:
        """Create sample YAML file contents."""
        base_path = Path("/data/input")
        return {
            base_path / "resume1.yaml": """
full_name: "John Doe"
email: "john@example.com"
config:
  template: "resume_no_bars"
  page_width: 210
  page_height: 297
  theme_color: "#0395DE"
description: "Professional developer"
""",
            base_path / "resume2.yaml": """
full_name: "Jane Smith"
email: "jane@example.com"
config:
  template: "resume_with_bars"
  page_width: 210
  page_height: 297
description: "Experienced designer"
""",
        }

    def test_generator_initialization_with_custom_deps(self) -> None:
        """Test generator initialization with custom dependencies."""
        custom_deps = GenerationDeps(
            pdf_writer=MockPdfWriter(),
            html_writer=MockHtmlWriter(),
            logger=MockLogger(),
            viewer=MockViewer(),
        )
        generator = ResumeGenerator(custom_deps)
        assert generator.deps == custom_deps

    def test_generator_initialization_with_defaults(self) -> None:
        """Test generator initialization with default dependencies."""
        generator = ResumeGenerator()
        assert isinstance(generator.deps.pdf_writer, WeasyPrintWriter)
        assert isinstance(generator.deps.html_writer, HtmlWriter)
        assert isinstance(generator.deps.logger, PrintLogger)
        assert isinstance(generator.deps.filesystem, LocalFileSystem)

    def test_generate_pdf_with_no_files(
        self, mock_deps: GenerationDeps, sample_paths: config.Paths
    ) -> None:
        """Test PDF generation when no YAML files exist."""
        generator = ResumeGenerator(mock_deps)

        # Create empty input directory
        mock_deps.filesystem.ensure_dir(sample_paths.input)

        with pytest.raises(FileNotFoundError, match="No YAML files found"):
            generator.generate_pdf(paths=sample_paths)

    def test_generate_html_with_no_files(
        self, mock_deps: GenerationDeps, sample_paths: config.Paths
    ) -> None:
        """Test HTML generation when no YAML files exist."""
        generator = ResumeGenerator(mock_deps)

        # Create empty input directory
        mock_deps.filesystem.ensure_dir(sample_paths.input)

        with pytest.raises(FileNotFoundError, match="No YAML files found"):
            generator.generate_html(paths=sample_paths)

    @patch("simple_resume.shell.generation.get_content")
    @patch("simple_resume.shell.generation.get_template_environment")
    def test_generate_pdf_single_resume(
        self,
        mock_get_template_env: Mock,
        mock_get_content: Mock,
        mock_deps: GenerationDeps,
        sample_paths: config.Paths,
    ) -> None:
        """Test successful PDF generation for a single resume."""
        # Setup mocks
        mock_get_content.return_value = {
            "full_name": "John Doe",
            "config": {
                "template": "resume_no_bars",
                "page_width": 210,
                "page_height": 297,
            },
            "description": "Professional developer",
        }

        mock_template = Mock()
        mock_template.render.return_value = "<html>Rendered content</html>"
        mock_env = Mock()
        mock_env.get_template.return_value = mock_template
        mock_get_template_env.return_value = mock_env

        # Create mock YAML file
        yaml_file = sample_paths.input / "resume1.yaml"
        mock_deps.filesystem.ensure_dir(sample_paths.input)
        mock_deps.filesystem.ensure_dir(sample_paths.output)

        # Mock the file collection
        with patch.object(
            generator := ResumeGenerator(mock_deps),
            "_collect_yaml_inputs",
            return_value=[yaml_file],
        ):
            generator.generate_pdf(paths=sample_paths)

        # Verify calls - check the writes list instead of calling assert_called_once
        assert len(mock_deps.pdf_writer.writes) == 1
        write_call = mock_deps.pdf_writer.writes[0]

        assert write_call["output_path"] == sample_paths.output / "resume1.pdf"
        assert write_call["html"] == "<html>Rendered content</html>"
        assert write_call["base_url"] == str(sample_paths.content)

        # Verify logging
        logger_events = mock_deps.logger.events
        assert len(logger_events) == 2
        assert logger_events[0]["type"] == "starting"
        assert logger_events[1]["type"] == "succeeded"

    @patch("simple_resume.shell.generation.get_content")
    @patch("simple_resume.shell.generation.get_template_environment")
    def test_generate_html_single_resume(
        self,
        mock_get_template_env: Mock,
        mock_get_content: Mock,
        mock_deps: GenerationDeps,
        sample_paths: config.Paths,
    ) -> None:
        """Test successful HTML generation for a single resume."""
        # Setup mocks
        mock_get_content.return_value = {
            "full_name": "John Doe",
            "config": {
                "template": "resume_no_bars",
                "page_width": 210,
                "page_height": 297,
            },
            "description": "Professional developer",
        }

        mock_template = Mock()
        mock_template.render.return_value = "<html>Rendered content</html>"
        mock_env = Mock()
        mock_env.get_template.return_value = mock_template
        mock_get_template_env.return_value = mock_env

        # Create mock YAML file
        yaml_file = sample_paths.input / "resume1.yaml"
        mock_deps.filesystem.ensure_dir(sample_paths.input)
        mock_deps.filesystem.ensure_dir(sample_paths.output)

        # Mock the file collection
        with patch.object(
            generator := ResumeGenerator(mock_deps),
            "_collect_yaml_inputs",
            return_value=[yaml_file],
        ):
            generator.generate_html(paths=sample_paths)

        # Verify calls - check the writes list instead of calling assert_called_once
        assert len(mock_deps.html_writer.writes) == 1
        write_call = mock_deps.html_writer.writes[0]

        assert write_call["output_path"] == sample_paths.output / "resume1.html"
        assert "<base href=" in write_call["html"]  # Base href should be injected

        # Verify logging
        logger_events = mock_deps.logger.events
        assert len(logger_events) == 2
        assert logger_events[0]["type"] == "starting"
        assert logger_events[1]["type"] == "succeeded"

    @patch("simple_resume.shell.generation.get_content")
    def test_generate_pdf_with_open_after(
        self,
        mock_get_content: Mock,
        mock_deps: GenerationDeps,
        sample_paths: config.Paths,
    ) -> None:
        """Test PDF generation with open_after=True."""
        # Setup mocks
        mock_get_content.return_value = {
            "full_name": "John Doe",
            "config": {"template": "resume_no_bars"},
        }

        yaml_file = sample_paths.input / "resume1.yaml"
        mock_deps.filesystem.ensure_dir(sample_paths.input)
        mock_deps.filesystem.ensure_dir(sample_paths.output)

        viewer = mock_deps.viewer
        assert isinstance(viewer, MockViewer)

        with patch.object(
            generator := ResumeGenerator(mock_deps),
            "_collect_yaml_inputs",
            return_value=[yaml_file],
        ):
            # Don't patch _execute_html_pdf_plan - we need it to run to test open_after
            with patch("simple_resume.shell.generation.get_template_environment"):
                generator.generate_pdf(paths=sample_paths, open_after=True)

        # Verify viewer was called
        assert len(viewer.opened_files) == 1

    @patch("simple_resume.shell.generation.get_content")
    def test_generate_html_with_browser(
        self,
        mock_get_content: Mock,
        mock_deps: GenerationDeps,
        sample_paths: config.Paths,
    ) -> None:
        """Test HTML generation with browser specification."""
        # Setup mocks
        mock_get_content.return_value = {
            "full_name": "John Doe",
            "config": {"template": "resume_no_bars"},
        }

        yaml_file = sample_paths.input / "resume1.yaml"
        mock_deps.filesystem.ensure_dir(sample_paths.input)
        mock_deps.filesystem.ensure_dir(sample_paths.output)

        with patch.object(
            generator := ResumeGenerator(mock_deps),
            "_collect_yaml_inputs",
            return_value=[yaml_file],
        ):
            # Don't patch _execute_html_plan - we need it to run to test open_after
            with patch("simple_resume.shell.generation.get_template_environment"):
                with patch.object(generator, "_open_in_browser") as mock_open_browser:
                    generator.generate_html(
                        paths=sample_paths, open_after=True, browser="firefox"
                    )
                    mock_open_browser.assert_called_once()

    def test_generate_pdf_with_invalid_data_dir(
        self, mock_deps: GenerationDeps
    ) -> None:
        """Test PDF generation with invalid data directory."""
        with pytest.raises(ValueError, match="Data directory does not exist"):
            generator = ResumeGenerator(mock_deps)
            generator.generate_pdf(data_dir="/nonexistent/path")

    def test_resolve_paths_conflicting_args(
        self, mock_deps: GenerationDeps, sample_paths: config.Paths
    ) -> None:
        """Test path resolution with conflicting arguments."""
        generator = ResumeGenerator(mock_deps)

        with pytest.raises(
            ValueError, match="Provide `paths` or individual overrides, not both"
        ):
            generator._resolve_paths(
                data_dir="/some/path",
                paths=sample_paths,
                overrides={"content_dir": "/other/path"},
            )

    def test_collect_yaml_inputs(
        self, mock_deps: GenerationDeps, sample_paths: config.Paths
    ) -> None:
        """Test YAML file collection from input directory."""
        generator = ResumeGenerator(mock_deps)

        # Setup mock files
        input_dir = sample_paths.input
        mock_deps.filesystem.ensure_dir(input_dir)

        # Create mock file objects
        mock_file1 = Mock()
        mock_file1.name = "resume1.yaml"
        mock_file1.is_file.return_value = True
        mock_file1.__str__ = lambda self: str(input_dir / "resume1.yaml")

        mock_file2 = Mock()
        mock_file2.name = "resume2.yml"
        mock_file2.is_file.return_value = True
        mock_file2.__str__ = lambda self: str(input_dir / "resume2.yml")

        mock_file3 = Mock()
        mock_file3.name = "resume3.txt"
        mock_file3.is_file.return_value = True

        # Create a mock iterdir that returns mock files
        def mock_iterdir(path: Path) -> list[Mock]:
            return [mock_file1, mock_file2, mock_file3]

        mock_deps.filesystem.iterdir = mock_iterdir  # type: ignore

        collected = generator._collect_yaml_inputs(input_dir)

        assert len(collected) == 2
        assert mock_file1 in collected
        assert mock_file2 in collected

    def test_determine_page_spec_from_config(self) -> None:
        """Test page specification extraction from config."""
        generator = ResumeGenerator()

        config = ResumeConfig(page_width=210, page_height=297)
        page_spec = generator._determine_page_spec(config)

        assert page_spec.width_mm == 210
        assert page_spec.height_mm == 297

    def test_determine_page_spec_with_defaults(self) -> None:
        """Test page specification extraction with defaults."""
        generator = ResumeGenerator()

        config = ResumeConfig()  # All defaults
        page_spec = generator._determine_page_spec(config)

        assert page_spec.width_mm == 190
        assert page_spec.height_mm == 270

    def test_inject_base_href(self) -> None:
        """Test base href injection into HTML."""
        generator = ResumeGenerator()
        base_path = Path("/test/path")

        html_without_head = "<html><body>Content</body></html>"
        result = generator._inject_base_href(html_without_head, base_path)
        assert result.startswith("<base href=")
        assert "Content" in result

        html_with_head = (
            "<html><head><title>Test</title></head><body>Content</body></html>"
        )
        result = generator._inject_base_href(html_with_head, base_path)
        assert "<head>\n  <base href=" in result
        assert "<title>Test</title>" in result
        assert "Content" in result

    def test_error_handling_during_generation(
        self, mock_deps: GenerationDeps, sample_paths: config.Paths
    ) -> None:
        """Test error handling during resume generation."""
        generator = ResumeGenerator(mock_deps)

        yaml_file = sample_paths.input / "invalid.yaml"
        mock_deps.filesystem.ensure_dir(sample_paths.input)
        mock_deps.filesystem.ensure_dir(sample_paths.output)

        # Mock get_content to raise an exception
        with patch.object(generator, "_collect_yaml_inputs", return_value=[yaml_file]):
            with patch(
                "simple_resume.shell.generation.get_content",
                side_effect=Exception("Test error"),
            ):
                generator.generate_pdf(paths=sample_paths)

        # Verify error was logged
        logger_events = mock_deps.logger.events
        assert len(logger_events) == 2
        assert logger_events[0]["type"] == "starting"
        assert logger_events[1]["type"] == "failed"
        assert "Test error" in str(logger_events[1]["error"])

    def test_execute_latex_plan_success(
        self,
        tmp_path: Path,
        story,
    ) -> None:
        story.given("a LaTeX render plan that compiles without errors")
        viewer = MockViewer()
        deps = GenerationDeps(
            pdf_writer=MockPdfWriter(),
            html_writer=MockHtmlWriter(),
            logger=MockLogger(),
            viewer=viewer,
            filesystem=MockFileSystem(),
        )
        generator = ResumeGenerator(deps)
        plan = RenderPlan(
            name="demo",
            mode="latex",
            config=ResumeConfig(output_mode="latex"),
            tex=r"\documentclass{article}",
            base_path=str(tmp_path),
        )
        output_file = tmp_path / "demo.pdf"

        with (
            patch(
                "simple_resume.shell.generation.compile_tex_to_pdf",
                return_value=output_file,
            ) as mock_compile,
            patch.object(generator, "_cleanup_latex_artifacts") as mock_cleanup,
        ):
            generator._execute_latex_plan(plan, output_file, open_after=True)

        story.then(
            "the compiler runs once, cleanup executes, and the viewer opens the PDF"
        )
        mock_compile.assert_called_once()
        mock_cleanup.assert_called_once()
        assert viewer.opened_files == [str(output_file)]
        tex_path = output_file.with_suffix(".tex")
        assert tex_path.read_text(encoding="utf-8") == r"\documentclass{article}"

    def test_execute_latex_plan_compilation_error_writes_log(
        self,
        tmp_path: Path,
        story,
    ) -> None:
        story.given("LaTeX compilation raises an error with diagnostic log text")
        viewer = MockViewer()
        deps = GenerationDeps(
            pdf_writer=MockPdfWriter(),
            html_writer=MockHtmlWriter(),
            logger=MockLogger(),
            viewer=viewer,
            filesystem=MockFileSystem(),
        )
        generator = ResumeGenerator(deps)
        plan = RenderPlan(
            name="broken",
            mode="latex",
            config=ResumeConfig(output_mode="latex"),
            tex="broken",
            base_path=str(tmp_path),
        )
        output_file = tmp_path / "broken.pdf"
        error = LatexCompilationError("boom", log="bad log")

        with (
            patch(
                "simple_resume.shell.generation.compile_tex_to_pdf",
                side_effect=error,
            ),
            patch.object(generator, "_cleanup_latex_artifacts") as mock_cleanup,
        ):
            with pytest.raises(LatexCompilationError):
                generator._execute_latex_plan(plan, output_file, open_after=False)

        story.then(
            "the LaTeX log is written beside the tex file and cleanup still runs"
        )
        log_path = output_file.with_suffix(".log")
        assert log_path.read_text(encoding="utf-8") == "bad log"
        mock_cleanup.assert_called_once()
        assert viewer.opened_files == []

    def test_execute_latex_html_plan_launches_browser(
        self,
        tmp_path: Path,
        story,
    ) -> None:
        story.given("a LaTeX render plan destined for HTML output")
        deps = GenerationDeps(
            pdf_writer=MockPdfWriter(),
            html_writer=MockHtmlWriter(),
            logger=MockLogger(),
            viewer=MockViewer(),
            filesystem=MockFileSystem(),
        )
        generator = ResumeGenerator(deps)
        plan = RenderPlan(
            name="demo",
            mode="latex",
            config=ResumeConfig(output_mode="latex"),
            tex="content",
            base_path=str(tmp_path),
        )
        output_file = tmp_path / "demo.html"

        with (
            patch(
                "simple_resume.shell.generation.compile_tex_to_html",
                return_value=output_file,
            ) as mock_compile,
            patch.object(generator, "_cleanup_latex_artifacts") as mock_cleanup,
            patch.object(generator, "_open_in_browser") as mock_open_in_browser,
        ):
            generator._execute_latex_html_plan(
                plan,
                output_file,
                open_after=True,
                browser="firefox",
            )

        story.then(
            "tex is converted once and the generated HTML is opened exactly once"
        )
        mock_compile.assert_called_once()
        mock_cleanup.assert_called_once()
        mock_open_in_browser.assert_called_once_with(output_file, "firefox")


class TestLocalFileSystem:
    """Test LocalFileSystem implementation."""

    def test_ensure_dir_creates_directory(self, tmp_path: Path) -> None:
        """Test directory creation."""
        fs = LocalFileSystem()
        test_dir = tmp_path / "test_dir"

        assert not test_dir.exists()
        fs.ensure_dir(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_dir_idempotent(self, tmp_path: Path) -> None:
        """Test that ensure_dir is idempotent."""
        fs = LocalFileSystem()
        test_dir = tmp_path / "test_dir"

        fs.ensure_dir(test_dir)
        fs.ensure_dir(test_dir)  # Should not raise
        assert test_dir.exists()

    def test_iterdir_returns_children(self, tmp_path: Path) -> None:
        """Test iterdir returns directory children."""
        fs = LocalFileSystem()

        # Create test files
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.txt").touch()
        (tmp_path / "subdir").mkdir()

        children = list(fs.iterdir(tmp_path))
        assert len(children) == 3
        assert tmp_path / "file1.txt" in children
        assert tmp_path / "file2.txt" in children
        assert tmp_path / "subdir" in children

    def test_is_dir_check(self, tmp_path: Path) -> None:
        """Test directory existence check."""
        fs = LocalFileSystem()

        file_path = tmp_path / "test_file.txt"
        dir_path = tmp_path / "test_dir"

        file_path.touch()
        dir_path.mkdir()

        assert fs.is_dir(dir_path) is True
        assert fs.is_dir(file_path) is False
        assert fs.is_dir(tmp_path / "nonexistent") is False


class TestPageSpec:
    """Test PageSpec dataclass."""

    def test_page_spec_creation(self) -> None:
        """Test PageSpec creation and immutability."""
        page_spec = PageSpec(width_mm=210, height_mm=297)

        assert page_spec.width_mm == 210
        assert page_spec.height_mm == 297

        with pytest.raises(FrozenInstanceError):
            page_spec.width_mm = 300

    def test_page_spec_equality(self) -> None:
        """Test PageSpec equality comparison."""
        spec1 = PageSpec(width_mm=210, height_mm=297)
        spec2 = PageSpec(width_mm=210, height_mm=297)
        spec3 = PageSpec(width_mm=210, height_mm=300)

        assert spec1 == spec2
        assert spec1 != spec3


class TestHtmlWriter:
    """Test HtmlWriter implementation."""

    def test_write_html_file(self, tmp_path: Path) -> None:
        """Test HTML file writing."""
        writer = HtmlWriter()
        output_path = tmp_path / "test.html"
        html_content = "<html><body>Test content</body></html>"

        writer.write(output_path=output_path, html=html_content)

        assert output_path.exists()
        assert output_path.read_text(encoding="utf-8") == html_content


class TestPrintLogger:
    """Test PrintLogger implementation."""

    def test_logging_methods(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test all logging methods."""
        logger = PrintLogger()
        test_path = Path("/test/output.pdf")
        test_error = Exception("Test error")

        logger.starting("test_resume", test_path)
        captured = capsys.readouterr()
        assert "-- Creating output.pdf --" in captured.out

        logger.succeeded("test_resume", test_path)
        captured = capsys.readouterr()
        assert "✓ Generated: /test/output.pdf" in captured.out

        logger.failed("test_resume", test_path, test_error)
        captured = capsys.readouterr()
        assert "✗ Failed to generate output.pdf: Test error" in captured.err


class TestShellHelpers:
    """Tests for lower-level helper methods in the shell generation module."""

    def test_cleanup_latex_artifacts_prunes_known_suffixes(
        self, tmp_path: Path, story
    ) -> None:
        story.given("LaTeX artifact files exist alongside the tex source")
        generator = ResumeGenerator()
        tex_path = tmp_path / "demo.tex"
        tex_path.write_text("document", encoding="utf-8")
        for suffix in (".aux", ".log", ".out"):
            (tmp_path / f"demo{suffix}").write_text("artifact", encoding="utf-8")

        generator._cleanup_latex_artifacts(tex_path)

        story.then("every recognised auxiliary file is removed")
        for suffix in (".aux", ".log", ".out"):
            assert not (tmp_path / f"demo{suffix}").exists()

    def test_cleanup_latex_artifacts_ignores_unlink_errors(
        self, tmp_path: Path, story
    ) -> None:
        story.given("deleting LaTeX artifacts raises OSError")
        generator = ResumeGenerator()
        tex_path = tmp_path / "demo.tex"
        artifact = tmp_path / "demo.aux"
        artifact.write_text("artifact", encoding="utf-8")

        with patch("pathlib.Path.unlink", side_effect=OSError("denied")) as mock_unlink:
            generator._cleanup_latex_artifacts(tex_path)

        story.then("errors are suppressed while unlink is still attempted")
        assert artifact.exists()
        assert mock_unlink.call_count >= 1

    def test_open_file_mac_invokes_open(self, tmp_path: Path, story) -> None:
        story.given("macOS environment with the open command available")
        generator = ResumeGenerator()
        pdf_path = str(tmp_path / "demo.pdf")

        with (
            patch("simple_resume.shell.generation.sys.platform", "darwin"),
            patch(
                "simple_resume.shell.generation.shutil.which",
                return_value="/usr/bin/open",
            ),
            patch("simple_resume.shell.generation.subprocess.Popen") as mock_popen,
        ):
            generator._open_file(pdf_path)

        story.then("the open command is launched exactly once")
        mock_popen.assert_called_once()
        assert pdf_path in mock_popen.call_args[0][0]

    def test_open_file_windows_uses_startfile(self, tmp_path: Path, story) -> None:
        story.given("Windows environment with os.startfile available")
        generator = ResumeGenerator()
        pdf_path = str(tmp_path / "demo.pdf")

        with (
            patch("simple_resume.shell.generation.sys.platform", "win32"),
            patch(
                "simple_resume.shell.generation.os.name",
                "nt",
            ),
            patch(
                "simple_resume.shell.generation.os.startfile", create=True
            ) as mock_startfile,
        ):
            generator._open_file(pdf_path)

        story.then("os.startfile receives the PDF path")
        mock_startfile.assert_called_once_with(pdf_path)

    def test_open_file_linux_with_xdg_open(self, tmp_path: Path, story) -> None:
        story.given("Linux environment with xdg-open available on PATH")
        generator = ResumeGenerator()
        pdf_path = str(tmp_path / "demo.pdf")

        with (
            patch("simple_resume.shell.generation.sys.platform", "linux"),
            patch(
                "simple_resume.shell.generation.os.name",
                "posix",
            ),
            patch(
                "simple_resume.shell.generation.shutil.which",
                return_value="/usr/bin/xdg-open",
            ),
            patch("simple_resume.shell.generation.subprocess.Popen") as mock_popen,
        ):
            generator._open_file(pdf_path)

        story.then("xdg-open launches with the pdf path")
        mock_popen.assert_called_once()
        assert pdf_path in mock_popen.call_args[0][0]

    def test_open_file_linux_without_xdg_open(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], story
    ) -> None:
        story.given("Linux environment without xdg-open installed")
        generator = ResumeGenerator()
        pdf_path = str(tmp_path / "demo.pdf")

        with (
            patch("simple_resume.shell.generation.sys.platform", "linux"),
            patch(
                "simple_resume.shell.generation.os.name",
                "posix",
            ),
            patch(
                "simple_resume.shell.generation.shutil.which",
                return_value=None,
            ),
        ):
            generator._open_file(pdf_path)

        story.then("a helpful tip is printed instead of raising")
        captured = capsys.readouterr()
        assert "xdg-utils" in captured.err

    def test_open_file_warns_on_exception(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], story
    ) -> None:
        story.given("subprocess launch unexpectedly fails")
        generator = ResumeGenerator()
        pdf_path = str(tmp_path / "demo.pdf")

        with (
            patch("simple_resume.shell.generation.sys.platform", "linux"),
            patch(
                "simple_resume.shell.generation.os.name",
                "posix",
            ),
            patch(
                "simple_resume.shell.generation.shutil.which",
                return_value="/usr/bin/xdg-open",
            ),
            patch(
                "simple_resume.shell.generation.subprocess.Popen",
                side_effect=RuntimeError("boom"),
            ),
        ):
            generator._open_file(pdf_path)

        story.then("a warning message is emitted to stderr")
        captured = capsys.readouterr()
        assert "Warning: Could not open" in captured.err

    def test_open_in_browser_explicit_command(self, tmp_path: Path, story) -> None:
        story.given("an explicit browser command is provided and exists on PATH")
        generator = ResumeGenerator()
        html_path = tmp_path / "index.html"

        def fake_which(name: str) -> str | None:
            return "/usr/bin/firefox" if name == "firefox" else None

        with (
            patch(
                "simple_resume.shell.generation.shutil.which",
                side_effect=fake_which,
            ),
            patch("simple_resume.shell.generation.subprocess.Popen") as mock_popen,
        ):
            generator._open_in_browser(html_path, "firefox")

        story.then("the explicit browser command is launched once with the HTML path")
        mock_popen.assert_called_once()
        assert mock_popen.call_args[0][0][-1] == str(html_path)

    def test_open_in_browser_picks_first_available_default(
        self, tmp_path: Path, story
    ) -> None:
        story.given("no browser hint is given but Chromium is installed")
        generator = ResumeGenerator()
        html_path = tmp_path / "index.html"

        def fake_which(name: str) -> str | None:
            return None if name == "firefox" else "/usr/bin/chromium"

        with (
            patch(
                "simple_resume.shell.generation.shutil.which",
                side_effect=fake_which,
            ),
            patch("simple_resume.shell.generation.subprocess.Popen") as mock_popen,
        ):
            generator._open_in_browser(html_path, None)

        story.then("Chromium is chosen automatically and launched once")
        mock_popen.assert_called_once()
        assert mock_popen.call_args[0][0][0] == "chromium"

    def test_open_in_browser_no_available_command(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], story
    ) -> None:
        story.given("no supported browser is present")
        generator = ResumeGenerator()
        html_path = tmp_path / "index.html"

        with patch("simple_resume.shell.generation.shutil.which", return_value=None):
            generator._open_in_browser(html_path, None)

        story.then("a tip is printed guiding the user to install a browser")
        captured = capsys.readouterr()
        assert "install Firefox or Chromium" in captured.err

    def test_open_in_browser_warns_on_failure(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], story
    ) -> None:
        story.given("launching the browser raises an unexpected error")
        generator = ResumeGenerator()
        html_path = tmp_path / "index.html"

        with (
            patch(
                "simple_resume.shell.generation.shutil.which",
                return_value="/usr/bin/firefox",
            ),
            patch(
                "simple_resume.shell.generation.subprocess.Popen",
                side_effect=RuntimeError("kaboom"),
            ),
        ):
            generator._open_in_browser(html_path, None)

        story.then("a warning is emitted about the failed browser launch")
        captured = capsys.readouterr()
        assert "Warning: could not launch" in captured.err
