"""Tests for shell PDF executor.

Following TDD principles - these tests are written BEFORE implementation.
Tests verify that PDF executor correctly executes effects and performs I/O.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from simple_resume.core.effects import Effect, MakeDirectory, WriteFile
from simple_resume.core.result import GenerationMetadata, GenerationResult
from simple_resume.shell.pdf_executor import execute_pdf_generation


class TestExecutePdfGeneration:
    """Tests for execute_pdf_generation function."""

    def test_executes_effects_and_returns_result(self, tmp_path: Path) -> None:
        """execute_pdf_generation runs effects and returns GenerationResult."""
        output_path = tmp_path / "resume.pdf"
        pdf_content = b"%PDF-1.4\nTest PDF content"

        effects = [
            MakeDirectory(path=output_path.parent),
            WriteFile(path=output_path, content=pdf_content),
        ]

        metadata = GenerationMetadata(
            format_type="pdf",
            template_name="html/demo.html",
            generation_time=0.0,
            file_size=0,
            resume_name="test_resume",
        )

        result = execute_pdf_generation(
            pdf_content=pdf_content,
            effects=effects,
            output_path=output_path,
            metadata=metadata,
        )

        # Should return GenerationResult
        assert isinstance(result, GenerationResult)
        assert result.output_path == output_path
        assert result.format_type == "pdf"
        assert result.metadata == metadata

        # Should have executed effects - PDF file should exist
        assert output_path.exists()
        assert output_path.read_bytes() == pdf_content

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """execute_pdf_generation creates nested parent directories."""
        output_path = tmp_path / "nested" / "dirs" / "resume.pdf"
        pdf_content = b"%PDF-1.4\nTest"

        effects = [
            MakeDirectory(path=output_path.parent, parents=True),
            WriteFile(path=output_path, content=pdf_content),
        ]

        metadata = GenerationMetadata(
            format_type="pdf",
            template_name="test",
            generation_time=0.0,
            file_size=0,
            resume_name="test",
        )

        result = execute_pdf_generation(
            pdf_content=pdf_content,
            effects=effects,
            output_path=output_path,
            metadata=metadata,
        )

        assert output_path.exists()
        assert output_path.parent.exists()
        assert result.output_path == output_path

    def test_uses_effect_executor(self, tmp_path: Path) -> None:
        """execute_pdf_generation uses EffectExecutor to run effects."""
        output_path = tmp_path / "resume.pdf"
        pdf_content = b"%PDF-1.4\nTest"

        effects = [
            MakeDirectory(path=output_path.parent),
            WriteFile(path=output_path, content=pdf_content),
        ]

        metadata = GenerationMetadata(
            format_type="pdf",
            template_name="test",
            generation_time=0.0,
            file_size=0,
            resume_name="test",
        )

        with patch("simple_resume.shell.pdf_executor.EffectExecutor") as MockExecutor:
            mock_executor_instance = MagicMock()
            MockExecutor.return_value = mock_executor_instance

            execute_pdf_generation(
                pdf_content=pdf_content,
                effects=effects,
                output_path=output_path,
                metadata=metadata,
            )

            # Should create EffectExecutor
            MockExecutor.assert_called_once()

            # Should call execute_many with effects
            mock_executor_instance.execute_many.assert_called_once_with(effects)

    def test_handles_empty_effects_list(self, tmp_path: Path) -> None:
        """execute_pdf_generation handles empty effects list gracefully."""
        output_path = tmp_path / "resume.pdf"
        pdf_content = b"%PDF-1.4\nTest"

        metadata = GenerationMetadata(
            format_type="pdf",
            template_name="test",
            generation_time=0.0,
            file_size=0,
            resume_name="test",
        )

        result = execute_pdf_generation(
            pdf_content=pdf_content,
            effects=[],  # Empty list
            output_path=output_path,
            metadata=metadata,
        )

        assert isinstance(result, GenerationResult)
        assert result.output_path == output_path

    def test_propagates_effect_execution_errors(self, tmp_path: Path) -> None:
        """execute_pdf_generation propagates errors from effect execution."""
        output_path = tmp_path / "resume.pdf"
        pdf_content = b"%PDF-1.4\nTest"

        # Create effect that will fail (directory without parents)
        effects: list[Effect] = [
            MakeDirectory(path=tmp_path / "nonexistent" / "child", parents=False),
        ]

        metadata = GenerationMetadata(
            format_type="pdf",
            template_name="test",
            generation_time=0.0,
            file_size=0,
            resume_name="test",
        )

        with pytest.raises(FileNotFoundError):
            execute_pdf_generation(
                pdf_content=pdf_content,
                effects=effects,
                output_path=output_path,
                metadata=metadata,
            )

    def test_returns_result_with_correct_metadata(self, tmp_path: Path) -> None:
        """execute_pdf_generation preserves metadata in result."""
        output_path = tmp_path / "resume.pdf"
        pdf_content = b"%PDF-1.4\nTest"

        palette_meta = {
            "source": "colourlovers",
            "palette_name": "Ocean",
            "colors": ["#1a2b3c"],
        }

        metadata = GenerationMetadata(
            format_type="pdf",
            template_name="html/demo.html",
            generation_time=1.23,
            file_size=5000,
            resume_name="john_doe",
            palette_info=palette_meta,
            page_count=2,
        )

        effects = [
            MakeDirectory(path=output_path.parent),
            WriteFile(path=output_path, content=pdf_content),
        ]

        result = execute_pdf_generation(
            pdf_content=pdf_content,
            effects=effects,
            output_path=output_path,
            metadata=metadata,
        )

        assert result.metadata is not None
        assert result.metadata.format_type == "pdf"
        assert result.metadata.template_name == "html/demo.html"
        assert result.metadata.resume_name == "john_doe"
        assert result.metadata.palette_info == palette_meta
        assert result.metadata.page_count == 2


class TestExecutePdfGenerationIntegration:
    """Integration tests for PDF generation execution."""

    def test_full_weasyprint_workflow(self, tmp_path: Path) -> None:
        """Test complete WeasyPrint PDF generation workflow."""
        output_path = tmp_path / "output" / "resume.pdf"

        # Simulate realistic PDF content
        pdf_content = (
            b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<\n/Type /Catalog\n>>\n"
            b"endobj\n%%EOF"
        )

        effects = [
            MakeDirectory(path=output_path.parent, parents=True),
            WriteFile(path=output_path, content=pdf_content),
        ]

        metadata = GenerationMetadata(
            format_type="pdf",
            template_name="html/demo.html",
            generation_time=0.5,
            file_size=len(pdf_content),
            resume_name="test_resume",
        )

        result = execute_pdf_generation(
            pdf_content=pdf_content,
            effects=effects,
            output_path=output_path,
            metadata=metadata,
        )

        # Verify result
        assert result.output_path == output_path
        assert result.format_type == "pdf"

        # Verify file was actually created
        assert output_path.exists()
        assert output_path.is_file()

        # Verify content
        actual_content = output_path.read_bytes()
        assert actual_content == pdf_content

    def test_latex_workflow_with_tex_and_pdf(self, tmp_path: Path) -> None:
        """Test LaTeX PDF generation workflow with intermediate .tex file."""
        output_path = tmp_path / "resume.pdf"
        tex_path = output_path.with_suffix(".tex")

        tex_content = (
            r"\documentclass{article}\begin{document}Test Resume\end{document}"
        )
        pdf_content = b"%PDF-1.4\nLaTeX generated PDF"

        effects = [
            MakeDirectory(path=output_path.parent),
            WriteFile(path=tex_path, content=tex_content, encoding="utf-8"),
            WriteFile(path=output_path, content=pdf_content),
        ]

        metadata = GenerationMetadata(
            format_type="pdf",
            template_name="resume.tex",
            generation_time=1.2,
            file_size=len(pdf_content),
            resume_name="latex_resume",
        )

        result = execute_pdf_generation(
            pdf_content=pdf_content,
            effects=effects,
            output_path=output_path,
            metadata=metadata,
        )

        # Both files should exist
        assert tex_path.exists()
        assert output_path.exists()

        # Verify content
        assert tex_path.read_text(encoding="utf-8") == tex_content
        assert output_path.read_bytes() == pdf_content

        assert result.output_path == output_path
