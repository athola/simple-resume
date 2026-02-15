"""Unit tests for CLI ATS scoring display and file reading helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from simple_resume.core.ats import ScorerResult, TournamentResult
from simple_resume.core.exceptions import ValidationError
from simple_resume.shell.cli import main as cli
from tests.bdd import Scenario

# ============================================================================
# File reading helpers
# ============================================================================


def test_read_file_text_pdf_raises_validation_error(
    tmp_path: Path, story: Scenario
) -> None:
    """Test that PDF files raise a user-friendly ValidationError."""
    story.given("a PDF file path")
    story.when("attempting to read it as job description text")

    pdf_file = tmp_path / "job.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

    with pytest.raises(ValidationError) as exc_info:
        cli._read_file_text(pdf_file)

    story.then("a ValidationError with helpful guidance is raised")
    assert ".pdf" in str(exc_info.value)
    assert "not yet supported" in str(exc_info.value)
    assert exc_info.value.errors is not None
    assert any("Supported formats" in e for e in exc_info.value.errors)


def test_read_file_text_html_raises_validation_error(
    tmp_path: Path, story: Scenario
) -> None:
    """Test that HTML files raise a user-friendly ValidationError."""
    story.given("an HTML file path")
    story.when("attempting to read it as job description text")

    html_file = tmp_path / "job.html"
    html_file.write_text("<html><body>Job posting</body></html>")

    with pytest.raises(ValidationError) as exc_info:
        cli._read_file_text(html_file)

    story.then("a ValidationError with helpful guidance is raised")
    assert ".html" in str(exc_info.value)
    assert "not yet supported" in str(exc_info.value)


def test_read_file_text_htm_raises_validation_error(
    tmp_path: Path, story: Scenario
) -> None:
    """Test that .htm files also raise a ValidationError."""
    story.given("a .htm file path")
    story.when("attempting to read it")

    htm_file = tmp_path / "job.htm"
    htm_file.write_text("<html><body>Job posting</body></html>")

    with pytest.raises(ValidationError) as exc_info:
        cli._read_file_text(htm_file)

    story.then("a ValidationError is raised")
    assert ".htm" in str(exc_info.value)


def test_read_file_text_txt_works(tmp_path: Path, story: Scenario) -> None:
    """Test that plain text files are read successfully."""
    story.given("a plain text job description file")
    story.when("reading it")

    txt_file = tmp_path / "job.txt"
    txt_file.write_text("Looking for a Python developer")

    content = cli._read_file_text(txt_file)

    story.then("the content is returned")
    assert content == "Looking for a Python developer"


def test_read_file_text_missing_file_raises_fnf(
    tmp_path: Path, story: Scenario
) -> None:
    """Test that missing files raise FileNotFoundError."""
    story.given("a non-existent file path")
    story.when("attempting to read it")

    missing = tmp_path / "nonexistent.txt"

    with pytest.raises(FileNotFoundError):
        cli._read_file_text(missing)

    story.then("FileNotFoundError is raised")


# ============================================================================
# ATS warnings and report formatting
# ============================================================================


def test_collect_ats_warnings_empty_result(story: Scenario) -> None:
    """Test that no warnings are collected from clean results."""
    story.given("a TournamentResult with no errors")
    result = TournamentResult(
        overall_score=0.75,
        algorithm_results=[],
        component_breakdown={},
        metadata={},
    )

    story.when("collecting warnings")
    warnings = cli._collect_ats_warnings(result)

    story.then("an empty list is returned")
    assert warnings == []


def test_collect_ats_warnings_from_algorithm_details(story: Scenario) -> None:
    """Test that warnings are collected from ScorerResult details."""
    story.given("a TournamentResult with error in algorithm details")
    scorer_result = ScorerResult(
        name="tfidf_cosine",
        score=0.5,
        weight=1.0,
        details={"error": "Fell back to permissive settings"},
    )
    result = TournamentResult(
        overall_score=0.5,
        algorithm_results=[scorer_result],
        metadata={},
    )

    story.when("collecting warnings")
    warnings = cli._collect_ats_warnings(result)

    story.then("the error is included in warnings")
    assert len(warnings) == 1
    assert "tfidf_cosine" in warnings[0]
    assert "Fell back" in warnings[0]


def test_collect_ats_warnings_from_metadata(story: Scenario) -> None:
    """Test that tournament-level errors are collected."""
    story.given("a TournamentResult with error in metadata")
    result = TournamentResult(
        overall_score=0.0,
        algorithm_results=[],
        metadata={"error": "All scorers failed"},
    )

    story.when("collecting warnings")
    warnings = cli._collect_ats_warnings(result)

    story.then("the tournament error is included")
    assert len(warnings) == 1
    assert "Tournament" in warnings[0]
    assert "All scorers failed" in warnings[0]


def test_format_text_report_includes_warnings(story: Scenario) -> None:
    """Test that _format_text_report includes WARNINGS section."""
    story.given("a TournamentResult with warnings")
    scorer_result = ScorerResult(
        name="test_scorer",
        score=0.5,
        weight=1.0,
        details={"error": "Test warning message"},
    )
    result = TournamentResult(
        overall_score=0.5,
        algorithm_results=[scorer_result],
        metadata={},
    )

    story.when("formatting the text report")
    report = cli._format_text_report(result, verbose=False)

    story.then("WARNINGS section is included")
    assert "WARNINGS" in report
    assert "Test warning message" in report


def test_format_text_report_includes_failed_scorers(story: Scenario) -> None:
    """Test that _format_text_report includes FAILED SCORERS section."""
    story.given("a TournamentResult with failed scorers")
    result = TournamentResult(
        overall_score=0.5,
        algorithm_results=[],
        failed_scorers=[("FailingScorer", "RuntimeError: Test failure")],
        metadata={},
    )

    story.when("formatting the text report")
    report = cli._format_text_report(result, verbose=False)

    story.then("FAILED SCORERS section is included")
    assert "FAILED SCORERS" in report
    assert "FailingScorer" in report
    assert "use --verbose" in report


def test_format_text_report_verbose_shows_error_details(story: Scenario) -> None:
    """Test that verbose mode shows full error details."""
    story.given("a TournamentResult with failed scorers")
    result = TournamentResult(
        overall_score=0.5,
        algorithm_results=[],
        failed_scorers=[("FailingScorer", "RuntimeError: Detailed error message")],
        metadata={},
    )

    story.when("formatting the text report in verbose mode")
    report = cli._format_text_report(result, verbose=True)

    story.then("full error message is shown")
    assert "FAILED SCORERS" in report
    assert "RuntimeError: Detailed error message" in report
