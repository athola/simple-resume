"""Unit tests for CLI job post tailoring subcommand."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest
import yaml

from simple_resume.shell.cli._tailor import (
    _extract_requirements_from_text,
    _load_job_posting,
    _load_resume_yaml,
    handle_tailor_command,
)
from tests.bdd import Scenario


class TestExtractRequirements:
    """Feature: Job requirements extraction from plain text.

    As a CLI user
    I want job posting text parsed into structured requirements
    So that gap analysis can be performed
    """

    @pytest.mark.unit
    def test_extracts_title_from_first_line(self, story: Scenario) -> None:
        """First line becomes the job title."""
        story.given("a job posting with a title on line 1")
        text = "Senior Python Developer\nPython\nDjango\nPostgreSQL"

        story.when("requirements are extracted")
        req = _extract_requirements_from_text(text)

        story.then("the title is the first line")
        assert req.title == "Senior Python Developer"
        assert "Python" in req.keywords

    @pytest.mark.unit
    def test_empty_text_uses_default_title(self, story: Scenario) -> None:
        """Empty text yields a default title."""
        story.given("an empty string")

        story.when("requirements are extracted")
        req = _extract_requirements_from_text("")

        story.then("the title is the default")
        assert req.title == "Unknown Position"


class TestLoadHelpers:
    """Feature: File loading helpers for tailor command.

    As the tailor command
    I want to load resume YAML and job posting text
    So that I can perform gap analysis
    """

    @pytest.mark.unit
    def test_load_resume_yaml(self, tmp_path: Path, story: Scenario) -> None:
        """Load a valid resume YAML file."""
        story.given("a valid resume YAML file")
        resume_file = tmp_path / "resume.yaml"
        data = {"full_name": "Test User", "job_title": "Developer"}
        resume_file.write_text(yaml.dump(data))

        story.when("loading the resume")
        result = _load_resume_yaml(resume_file)

        story.then("the parsed dict is returned")
        assert result["full_name"] == "Test User"

    @pytest.mark.unit
    def test_load_resume_yaml_missing(self, tmp_path: Path, story: Scenario) -> None:
        """Loading a missing resume file raises FileNotFoundError."""
        story.given("a nonexistent resume path")
        with pytest.raises(FileNotFoundError):
            _load_resume_yaml(tmp_path / "missing.yaml")
        story.then("FileNotFoundError is raised")

    @pytest.mark.unit
    def test_load_job_posting(self, tmp_path: Path, story: Scenario) -> None:
        """Load a valid job posting file."""
        story.given("a job posting text file")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Senior Engineer\nPython required")

        story.when("loading the job posting")
        result = _load_job_posting(job_file)

        story.then("the text is returned")
        assert "Senior Engineer" in result

    @pytest.mark.unit
    def test_load_job_posting_missing(self, tmp_path: Path, story: Scenario) -> None:
        """Loading a missing job posting raises FileNotFoundError."""
        story.given("a nonexistent job posting path")
        with pytest.raises(FileNotFoundError):
            _load_job_posting(tmp_path / "missing.txt")
        story.then("FileNotFoundError is raised")


class TestHandleTailorCommand:
    """Feature: Resume tailoring CLI command.

    As a job seeker
    I want to compare my resume against a job posting
    So that I can see what gaps to fill
    """

    @pytest.mark.unit
    def test_tailor_report_only(self, tmp_path: Path, story: Scenario) -> None:
        """Run tailor with --report flag for gap analysis only."""
        story.given("a resume YAML and job posting")

        resume_file = tmp_path / "resume.yaml"
        resume_data = {
            "full_name": "Jane Doe",
            "job_title": "Python Developer",
            "keyskills": ["Python", "Django", "PostgreSQL"],
            "body": {
                "Experience": [
                    {
                        "title": "Developer",
                        "company": "Acme",
                        "description": "Built web apps with Python and Django",
                    }
                ]
            },
        }
        resume_file.write_text(yaml.dump(resume_data))

        job_file = tmp_path / "job.txt"
        job_file.write_text(
            "Senior Python Developer\nPython\nDjango\nKubernetes\nAWS\n"
        )

        args = argparse.Namespace(
            command="tailor",
            resume=resume_file,
            job=job_file,
            api_key=None,
            model=None,
            report=True,
        )

        story.when("the tailor command is run with --report")
        result = handle_tailor_command(args)

        story.then("exit code is 0")
        assert result == 0

    @pytest.mark.unit
    def test_tailor_missing_resume(self, tmp_path: Path, story: Scenario) -> None:
        """Tailor with a missing resume file returns exit code 1."""
        story.given("a nonexistent resume file")

        job_file = tmp_path / "job.txt"
        job_file.write_text("Some job posting")

        args = argparse.Namespace(
            command="tailor",
            resume=tmp_path / "missing.yaml",
            job=job_file,
            api_key=None,
            model=None,
            report=True,
        )

        story.when("the tailor command is run")
        result = handle_tailor_command(args)

        story.then("exit code is 1")
        assert result == 1

    @pytest.mark.unit
    def test_tailor_missing_job(self, tmp_path: Path, story: Scenario) -> None:
        """Tailor with a missing job posting file returns exit code 1."""
        story.given("a valid resume but missing job posting")

        resume_file = tmp_path / "resume.yaml"
        resume_file.write_text(yaml.dump({"full_name": "Test"}))

        args = argparse.Namespace(
            command="tailor",
            resume=resume_file,
            job=tmp_path / "missing.txt",
            api_key=None,
            model=None,
            report=True,
        )

        story.when("the tailor command is run")
        result = handle_tailor_command(args)

        story.then("exit code is 1")
        assert result == 1

    @pytest.mark.unit
    def test_tailor_no_api_key_without_report(
        self, tmp_path: Path, story: Scenario
    ) -> None:
        """Tailor without --report and without API key returns exit code 1."""
        story.given("resume and job posting but no API key")

        resume_file = tmp_path / "resume.yaml"
        resume_file.write_text(yaml.dump({"full_name": "Test"}))

        job_file = tmp_path / "job.txt"
        job_file.write_text("Senior Dev\nPython\n")

        args = argparse.Namespace(
            command="tailor",
            resume=resume_file,
            job=job_file,
            api_key=None,
            model=None,
            report=False,
        )

        story.when("the tailor command is run without API key")
        # Clear any env vars that might provide a key
        import os  # noqa: PLC0415

        env_keys = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GOOGLE_API_KEY",
            "MISTRAL_API_KEY",
            "COHERE_API_KEY",
        ]
        saved = {k: os.environ.pop(k, None) for k in env_keys}
        try:
            result = handle_tailor_command(args)
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v

        story.then("exit code is 1")
        assert result == 1
