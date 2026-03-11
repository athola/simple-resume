"""Unit tests for CLI ATS scoring display and file reading helpers."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from simple_resume.core.ats import ATSTournament, ScorerResult, TournamentResult
from simple_resume.core.exceptions import ValidationError
from simple_resume.shell.cli import main as cli
from simple_resume.shell.cli._screen import (
    _build_tournament,
    _collect_resume_files,
    _format_text_report,
    _get_status_label,
    _output_report,
    handle_screen_command,
)
from tests.bdd import Scenario


def _make_screen_args(**kwargs: object) -> argparse.Namespace:
    """Build a minimal argparse.Namespace for screen commands."""
    defaults = {
        "resume": None,
        "job": None,
        "output": None,
        "format": "text",
        "scorers": "all",
        "verbose": False,
        "batch": False,
        "top": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


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


# ============================================================================
# Tournament builder
# ============================================================================


class TestBuildTournament:
    """_build_tournament selects the correct scorer(s) by name."""

    @pytest.mark.parametrize(
        ("selection", "expected_scorer"),
        [
            ("tfidf", "tfidf"),
            ("jaccard", "jaccard"),
            ("keyword", "keyword"),
        ],
    )
    def test_individual_scorer_selection(
        self, story: Scenario, selection: str, expected_scorer: str
    ) -> None:
        story.given(f"scorer selection '{selection}'")
        story.when("building a tournament")
        tournament = _build_tournament(selection)

        story.then(f"only the {expected_scorer} scorer is included")
        assert len(tournament.scorers) == 1
        assert expected_scorer in type(tournament.scorers[0]).__name__.lower()

    def test_all_scorers_selection(self, story: Scenario) -> None:
        story.given("scorer selection 'all'")
        story.when("building a tournament")
        tournament = _build_tournament("all")

        story.then("multiple scorers are included (default set)")
        assert len(tournament.scorers) >= 2


# ============================================================================
# Resume file collector
# ============================================================================


class TestCollectResumeFiles:
    """_collect_resume_files finds files with valid resume suffixes."""

    def test_collects_supported_suffixes(self, tmp_path: Path, story: Scenario) -> None:
        story.given("a directory with .txt, .md, .yaml, .json, and .py files")
        for name in ["a.txt", "b.md", "c.yaml", "d.json", "e.py", "f.yml"]:
            (tmp_path / name).write_text("content")

        story.when("collecting resume files")
        files = _collect_resume_files(tmp_path)

        story.then("only files with resume suffixes are returned")
        names = [f.name for f in files]
        assert "a.txt" in names
        assert "b.md" in names
        assert "c.yaml" in names
        assert "d.json" in names
        assert "f.yml" in names
        assert "e.py" not in names

    def test_returns_sorted_list(self, tmp_path: Path, story: Scenario) -> None:
        story.given("a directory with resume files in random order")
        for name in ["z.txt", "a.txt", "m.txt"]:
            (tmp_path / name).write_text("content")

        story.when("collecting resume files")
        files = _collect_resume_files(tmp_path)

        story.then("files are returned in sorted order")
        assert [f.name for f in files] == ["a.txt", "m.txt", "z.txt"]


# ============================================================================
# Output report (file vs stdout)
# ============================================================================


class TestOutputReport:
    """_output_report writes to file or prints to stdout."""

    def test_prints_to_stdout_when_no_path(
        self, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("report content and no output path")
        story.when("outputting the report")
        _output_report("report text here", None)

        story.then("the report is printed to stdout")
        assert "report text here" in capsys.readouterr().out

    def test_writes_to_file_when_path_given(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("report content and an output file path")
        out_file = tmp_path / "reports" / "result.txt"

        story.when("outputting the report")
        _output_report("saved report", out_file)

        story.then("the report is written to the file and a confirmation is printed")
        assert out_file.read_text() == "saved report"
        assert "Report saved" in capsys.readouterr().out


# ============================================================================
# Single-mode screen command
# ============================================================================


class TestSingleModeScreen:
    """handle_screen_command in single (non-batch) mode."""

    def test_screens_single_resume_successfully(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("a resume file and a job description with overlapping keywords")
        resume = tmp_path / "resume.txt"
        resume.write_text("Experienced Python developer with Django and REST APIs.")
        job = tmp_path / "job.txt"
        job.write_text("Looking for a Python developer with Django experience.")

        story.when("running single-mode screen")
        args = _make_screen_args(resume=resume, job=job)
        exit_code = handle_screen_command(args)

        story.then("a text report is printed with a score")
        output = capsys.readouterr().out
        assert "ATS SCORING REPORT" in output
        assert "Overall Score" in output
        assert exit_code in (0, 1)  # depends on score threshold

    def test_empty_job_file_returns_error(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("a resume and an empty job description file")
        resume = tmp_path / "resume.txt"
        resume.write_text("Python developer")
        job = tmp_path / "job.txt"
        job.write_text("   ")

        story.when("running single-mode screen")
        args = _make_screen_args(resume=resume, job=job)
        exit_code = handle_screen_command(args)

        story.then("an error about empty job description is returned")
        output = capsys.readouterr().out
        assert exit_code == 1
        assert "empty" in output.lower()

    def test_empty_resume_returns_error(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("an empty resume file and a valid job description")
        resume = tmp_path / "resume.txt"
        resume.write_text("")
        job = tmp_path / "job.txt"
        job.write_text("Python developer needed.")

        story.when("running single-mode screen")
        args = _make_screen_args(resume=resume, job=job)
        exit_code = handle_screen_command(args)

        story.then("an error about empty resume is returned")
        output = capsys.readouterr().out
        assert exit_code == 1
        assert "empty" in output.lower()

    def test_yaml_report_format(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("a resume and job with --format yaml")
        resume = tmp_path / "resume.txt"
        resume.write_text("Python developer with 5 years experience in web apps.")
        job = tmp_path / "job.txt"
        job.write_text("Senior Python developer for web application development.")

        story.when("running screen with yaml format")
        args = _make_screen_args(resume=resume, job=job, format="yaml")
        exit_code = handle_screen_command(args)

        story.then("YAML-formatted output is produced")
        output = capsys.readouterr().out
        assert exit_code in (0, 1)
        # YAML output should not have the text report header
        assert "ATS SCORING REPORT" not in output

    def test_json_report_format(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("a resume and job with --format json")
        resume = tmp_path / "resume.txt"
        resume.write_text("Python developer with 5 years experience in web apps.")
        job = tmp_path / "job.txt"
        job.write_text("Senior Python developer for web application development.")

        story.when("running screen with json format")
        args = _make_screen_args(resume=resume, job=job, format="json")
        exit_code = handle_screen_command(args)

        story.then("JSON-formatted output is produced")
        output = capsys.readouterr().out
        assert exit_code in (0, 1)
        assert "ATS SCORING REPORT" not in output

    def test_output_to_file(self, tmp_path: Path, story: Scenario) -> None:
        story.given("a resume, job, and --output flag")
        resume = tmp_path / "resume.txt"
        resume.write_text("Python developer experienced in machine learning.")
        job = tmp_path / "job.txt"
        job.write_text("ML engineer with Python experience needed.")
        out_file = tmp_path / "report.txt"

        story.when("running screen with output path")
        args = _make_screen_args(resume=resume, job=job, output=out_file)
        exit_code = handle_screen_command(args)

        story.then("report is saved to the output file")
        assert exit_code in (0, 1)
        assert out_file.exists()
        assert "ATS SCORING REPORT" in out_file.read_text()


# ============================================================================
# Status labels
# ============================================================================


class TestGetStatusLabel:
    """_get_status_label returns the correct label for score ranges."""

    @pytest.mark.parametrize(
        ("score", "expected_fragment"),
        [
            (90, "Excellent"),
            (80, "Excellent"),
            (70, "Good"),
            (65, "Good"),
            (55, "Fair"),
            (50, "Fair"),
            (40, "Poor"),
            (35, "Poor"),
            (20, "Very Poor"),
            (0, "Very Poor"),
        ],
    )
    def test_score_thresholds(
        self, story: Scenario, score: float, expected_fragment: str
    ) -> None:
        story.given(f"a score of {score}")
        story.when("getting the status label")
        label = _get_status_label(score)

        story.then(f"the label contains '{expected_fragment}'")
        assert expected_fragment in label


# ============================================================================
# Verbose report formatting
# ============================================================================


class TestVerboseTextReport:
    """Verbose text report includes cosine, shared keywords, and components."""

    def test_verbose_shows_cosine_similarity(self, story: Scenario) -> None:
        story.given("a result with cosine_similarity in algorithm details")
        scorer_result = ScorerResult(
            name="tfidf",
            score=0.7,
            weight=1.0,
            details={"cosine_similarity": 0.6543},
        )
        result = TournamentResult(
            overall_score=0.7,
            algorithm_results=[scorer_result],
            metadata={},
        )

        story.when("formatting the text report in verbose mode")
        report = _format_text_report(result, verbose=True)

        story.then("the cosine similarity value is shown")
        assert "Cosine" in report
        assert "0.6543" in report

    def test_verbose_shows_shared_keywords_count(self, story: Scenario) -> None:
        story.given("a result with shared_keywords in algorithm details")
        scorer_result = ScorerResult(
            name="keyword",
            score=0.6,
            weight=1.0,
            details={"shared_keywords": ["python", "django", "rest"]},
        )
        result = TournamentResult(
            overall_score=0.6,
            algorithm_results=[scorer_result],
            metadata={},
        )

        story.when("formatting the text report in verbose mode")
        report = _format_text_report(result, verbose=True)

        story.then("the shared keywords count is shown")
        assert "Shared" in report
        assert "3 keywords" in report

    def test_verbose_shows_component_breakdown(self, story: Scenario) -> None:
        story.given("a result with component breakdown")
        result = TournamentResult(
            overall_score=0.65,
            algorithm_results=[],
            component_breakdown={"skills": 0.8, "experience": 0.5},
            metadata={},
        )

        story.when("formatting the text report in verbose mode")
        report = _format_text_report(result, verbose=True)

        story.then("the component scores section is shown")
        assert "COMPONENT SCORES" in report
        assert "skills" in report
        assert "experience" in report

    def test_non_verbose_hides_components(self, story: Scenario) -> None:
        story.given("a result with component breakdown")
        result = TournamentResult(
            overall_score=0.65,
            algorithm_results=[],
            component_breakdown={"skills": 0.8},
            metadata={},
        )

        story.when("formatting the text report in non-verbose mode")
        report = _format_text_report(result, verbose=False)

        story.then("the component scores section is NOT shown")
        assert "COMPONENT SCORES" not in report


# ============================================================================
# Latin-1 encoding fallback
# ============================================================================


class TestReadFileTextEncoding:
    """_read_file_text falls back to latin-1 for non-UTF-8 files."""

    def test_latin1_fallback(self, tmp_path: Path, story: Scenario) -> None:
        story.given("a text file with latin-1 encoded characters")
        latin1_file = tmp_path / "resume.txt"
        latin1_file.write_bytes("Résumé with café".encode("latin-1"))

        story.when("reading the file")
        content = cli._read_file_text(latin1_file)

        story.then("the content is read using latin-1 fallback")
        assert "caf" in content

    def test_latin1_fallback_emits_warning(
        self, tmp_path: Path, story: Scenario
    ) -> None:
        story.given("a text file with latin-1 encoded characters")
        latin1_file = tmp_path / "resume.txt"
        latin1_file.write_bytes("Résumé with café".encode("latin-1"))

        story.when("reading the file")
        with pytest.warns(UserWarning, match="latin-1"):
            content = cli._read_file_text(latin1_file)

        story.then("a warning is emitted and the content is read")
        assert "caf" in content


# ============================================================================
# Error handling in screen command
# ============================================================================


class TestScreenErrorHandling:
    """Error paths in handle_screen_command."""

    def test_single_mode_catches_domain_error(
        self,
        tmp_path: Path,
        story: Scenario,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        story.given("a resume that triggers a SimpleResumeError during screening")
        resume = tmp_path / "resume.pdf"
        resume.write_bytes(b"%PDF fake")
        job = tmp_path / "job.txt"
        job.write_text("Python developer needed.")

        story.when("running single-mode screen with a PDF resume")
        args = _make_screen_args(resume=resume, job=job)
        exit_code = handle_screen_command(args)

        story.then("the error is caught and printed")
        output = capsys.readouterr().out
        assert exit_code == 1
        assert "error" in output.lower() or "Error" in output

    def test_batch_mode_skips_resume_with_scoring_failure(
        self,
        tmp_path: Path,
        story: Scenario,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        story.given("a directory where one resume causes a scoring exception")
        resumes_dir = tmp_path / "resumes"
        resumes_dir.mkdir()
        (resumes_dir / "good.txt").write_text("Python developer with experience.")
        (resumes_dir / "bad.txt").write_text("This will fail during scoring.")

        job = tmp_path / "job.txt"
        job.write_text("Python developer needed.")

        # Make the tournament's score method fail for one specific input
        original_score = ATSTournament.score
        call_count = 0

        def failing_score(self, resume_text, job_text):  # type: ignore[no-untyped-def]
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Simulated scoring failure")
            return original_score(self, resume_text, job_text)

        monkeypatch.setattr(ATSTournament, "score", failing_score)

        story.when("running batch screen")
        args = _make_screen_args(resume=resumes_dir, job=job, batch=True)
        exit_code = handle_screen_command(args)

        story.then("the failing resume is skipped and the good one is scored")
        output = capsys.readouterr().out
        assert exit_code == 0
        assert "scoring failed" in output.lower() or "Skipping" in output
