"""Tests for batch screening CLI feature (issue #7).

Covers batch mode: screening multiple resumes against a single job
description, ranking them, and returning top-N results.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from simple_resume.core.ats import TournamentResult
from simple_resume.shell.cli._screen import (
    _format_batch_report,
    handle_screen_command,
)
from tests.bdd import Scenario


def _make_tournament_result(overall_score: float) -> TournamentResult:
    """Build a minimal TournamentResult for use in unit tests."""
    return TournamentResult(
        overall_score=overall_score,
        algorithm_results=[],
        component_breakdown={},
        metadata={},
        failed_scorers=[],
    )


def _make_args(**kwargs):  # type: ignore[no-untyped-def]
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


class TestBatchScreeningCLI:
    """Batch screening: multiple resumes vs. one job description."""

    def test_batch_mode_scores_all_resumes_in_directory(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("a directory with 3 resume files and a job description")
        resumes_dir = tmp_path / "resumes"
        resumes_dir.mkdir()
        skills = ["Python developer", "Java developer", "Go developer"]
        for i, skill in enumerate(skills):
            (resumes_dir / f"resume_{i}.txt").write_text(
                f"Experienced {skill} with 5 years of experience."
            )
        job_file = tmp_path / "job.txt"
        job_file.write_text("Looking for a Python developer with experience.")

        story.when("running batch screen")
        args = _make_args(resume=resumes_dir, job=job_file, batch=True)
        exit_code = handle_screen_command(args)

        story.then("all resumes are scored and a ranked report is printed")
        output = capsys.readouterr().out
        assert exit_code == 0
        assert "BATCH" in output.upper()
        assert "resume_0" in output
        assert "resume_1" in output
        assert "resume_2" in output

    def test_batch_mode_top_n_limits_results(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("a directory with 5 resumes and --top 2")
        resumes_dir = tmp_path / "resumes"
        resumes_dir.mkdir()
        for i in range(5):
            (resumes_dir / f"resume_{i}.txt").write_text(
                f"Engineer #{i} skilled in Python and data pipelines."
            )
        job_file = tmp_path / "job.txt"
        job_file.write_text("Python data engineer needed.")

        story.when("running batch screen with top=2")
        args = _make_args(resume=resumes_dir, job=job_file, batch=True, top=2)
        exit_code = handle_screen_command(args)

        story.then("only 2 results are shown")
        output = capsys.readouterr().out
        assert exit_code == 0
        # Count ranked entries (lines with "resume_" in ranked output)
        ranked_lines = [
            line
            for line in output.splitlines()
            if line.strip().startswith(("1.", "2.", "3.", "4.", "5."))
        ]
        assert len(ranked_lines) == 2

    def test_batch_mode_empty_directory_returns_error(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("an empty directory")
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        job_file = tmp_path / "job.txt"
        job_file.write_text("Python developer needed.")

        story.when("running batch screen on empty directory")
        args = _make_args(resume=empty_dir, job=job_file, batch=True)
        exit_code = handle_screen_command(args)

        story.then("an error is returned")
        output = capsys.readouterr().out
        assert exit_code == 1
        assert "no resume" in output.lower()

    def test_batch_mode_skips_unreadable_files(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("a directory with one good and one unreadable resume")
        resumes_dir = tmp_path / "resumes"
        resumes_dir.mkdir()
        (resumes_dir / "good.txt").write_text("Python developer with 5 years exp.")
        bad = resumes_dir / "bad.txt"
        bad.write_text("content")
        bad.chmod(0o000)

        job_file = tmp_path / "job.txt"
        job_file.write_text("Python developer needed.")

        story.when("running batch screen")
        args = _make_args(resume=resumes_dir, job=job_file, batch=True)
        exit_code = handle_screen_command(args)

        story.then("the good file is scored and the bad file is skipped")
        bad.chmod(0o644)  # restore for cleanup
        output = capsys.readouterr().out
        assert exit_code == 0
        assert "good" in output
        assert "Skipping" in output

    def test_batch_mode_file_instead_of_directory_returns_error(
        self, tmp_path: Path, story: Scenario
    ) -> None:
        story.given("a file path instead of a directory")
        resume_file = tmp_path / "single_resume.txt"
        resume_file.write_text("Python developer with 5 years experience.")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Python developer needed.")

        story.when("running batch screen with a file path")
        args = _make_args(resume=resume_file, job=job_file, batch=True)
        exit_code = handle_screen_command(args)

        story.then("an error is returned because batch requires a directory")
        assert exit_code == 1

    def test_batch_mode_all_empty_resumes_returns_error(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("a directory where all resume files are empty")
        resumes_dir = tmp_path / "resumes"
        resumes_dir.mkdir()
        (resumes_dir / "empty_a.txt").write_text("   ")
        (resumes_dir / "empty_b.txt").write_text("")

        job_file = tmp_path / "job.txt"
        job_file.write_text("Python developer needed.")

        story.when("running batch screen")
        args = _make_args(resume=resumes_dir, job=job_file, batch=True)
        exit_code = handle_screen_command(args)

        story.then("an error is returned because no files could be scored")
        output = capsys.readouterr().out
        assert exit_code == 1
        assert "no resume" in output.lower()

    def test_batch_mode_nonexistent_directory_returns_error(
        self, tmp_path: Path, story: Scenario
    ) -> None:
        story.given("a non-existent directory")
        missing = tmp_path / "missing"
        job_file = tmp_path / "job.txt"
        job_file.write_text("Python developer needed.")

        story.when("running batch screen on missing directory")
        args = _make_args(resume=missing, job=job_file, batch=True)
        exit_code = handle_screen_command(args)

        story.then("an error is returned")
        assert exit_code == 1


class TestBatchReportFormatting:
    """Batch report output formatting."""

    def test_format_batch_report_ranks_by_score(self, story: Scenario) -> None:
        story.given("batch results with varying scores")
        results = [
            ("resume_c.txt", _make_tournament_result(0.9)),
            ("resume_a.txt", _make_tournament_result(0.5)),
            ("resume_b.txt", _make_tournament_result(0.7)),
        ]

        story.when("formatting the batch report")
        report = _format_batch_report(results, "job.txt")

        story.then("results are sorted by score descending")
        lines = report.splitlines()
        ranked = [ln for ln in lines if ln.strip().startswith(("1.", "2.", "3."))]
        assert len(ranked) == 3
        assert "resume_c" in ranked[0]
        assert "resume_b" in ranked[1]
        assert "resume_a" in ranked[2]

    def test_format_batch_report_includes_header(self, story: Scenario) -> None:
        story.given("batch results")
        results = [("resume.txt", _make_tournament_result(0.75))]

        story.when("formatting the batch report")
        report = _format_batch_report(results, "job.txt")

        story.then("the report includes a header")
        assert "BATCH" in report.upper()
        assert "job.txt" in report


class TestBatchFormatVerbose:
    """Batch mode respects --format and --verbose flags (#105)."""

    def test_batch_json_format(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("a directory with resumes and --format json")
        resumes_dir = tmp_path / "resumes"
        resumes_dir.mkdir()
        (resumes_dir / "resume_a.txt").write_text("Python developer with Django.")
        (resumes_dir / "resume_b.txt").write_text("Java developer with Spring.")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Looking for a Python developer.")

        story.when("running batch screen with json format")
        args = _make_args(resume=resumes_dir, job=job_file, batch=True, format="json")
        exit_code = handle_screen_command(args)

        story.then("valid JSON is produced with results array")
        output = capsys.readouterr().out
        assert exit_code == 0
        data = json.loads(output)
        assert "results" in data
        assert len(data["results"]) == 2

    def test_batch_yaml_format(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("a directory with resumes and --format yaml")
        resumes_dir = tmp_path / "resumes"
        resumes_dir.mkdir()
        (resumes_dir / "resume_a.txt").write_text("Python developer with Django.")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Looking for a Python developer.")

        story.when("running batch screen with yaml format")
        args = _make_args(resume=resumes_dir, job=job_file, batch=True, format="yaml")
        exit_code = handle_screen_command(args)

        story.then("YAML output is produced without text report header")
        output = capsys.readouterr().out
        assert exit_code == 0
        assert "BATCH ATS SCREENING REPORT" not in output
        assert "results:" in output or "overall_score" in output

    def test_batch_verbose_text_shows_algorithm_breakdown(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("a directory with resumes and --verbose flag")
        resumes_dir = tmp_path / "resumes"
        resumes_dir.mkdir()
        (resumes_dir / "resume_a.txt").write_text("Python developer with 5 years.")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Senior Python developer needed.")

        story.when("running batch screen with verbose")
        args = _make_args(resume=resumes_dir, job=job_file, batch=True, verbose=True)
        exit_code = handle_screen_command(args)

        story.then("algorithm details are shown in the report")
        output = capsys.readouterr().out
        assert exit_code == 0
        assert "tfidf" in output.lower() or "keyword" in output.lower()
