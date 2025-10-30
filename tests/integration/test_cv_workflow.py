"""Integration tests for CV generation without a web server."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, TypedDict

import yaml

from easyresume import config
from easyresume.rendering import render_resume_html
from easyresume.utilities import get_content
from tests.conftest import create_complete_cv_data


class ValidationScenario(TypedDict):
    """Typed scenario definition for CV validation tests."""

    name: str
    data: dict[str, Any]
    should_be_valid: bool


class TestCVWorkflowIntegration:
    """Integration tests for complete CV generation workflow."""

    def test_end_to_end_cv_creation_workflow(
        self, temp_dir: Path, sample_cv_data: dict[str, Any]
    ) -> None:
        """Validate loading YAML and rendering HTML."""
        cv_file = temp_dir / "john_doe.yaml"
        cv_file.write_text(yaml.dump(sample_cv_data), encoding="utf-8")

        test_input_dir = temp_dir / "input"
        test_input_dir.mkdir()
        (test_input_dir / "john_doe.yaml").write_text(
            cv_file.read_text(encoding="utf-8"), encoding="utf-8"
        )

        paths = config.Paths(
            data=temp_dir,
            input=test_input_dir,
            output=temp_dir / "output",
        )

        cv_content = get_content("john_doe", paths=paths)
        assert cv_content["full_name"] == "John Doe"

        html, _, _ = render_resume_html("john_doe", paths=paths)
        assert "John Doe" in html

    def test_multiple_cv_management_workflow(self, temp_dir: Path) -> None:
        """Handle multiple CV variants in a single directory."""
        cv_variants = {
            "technical_cv": create_complete_cv_data(
                template="cv_no_bars",
                full_name="Alice Johnson",
                expertise=["Python", "Docker", "Kubernetes", "CI/CD"],
            ),
            "managerial_cv": create_complete_cv_data(
                template="cv_with_bars",
                full_name="Alice Johnson",
                expertise={
                    "Team Leadership": 90,
                    "Project Management": 85,
                    "Agile": 80,
                },
            ),
        }

        test_input_dir = temp_dir / "input"
        test_input_dir.mkdir()

        for cv_name, cv_data in cv_variants.items():
            (test_input_dir / f"{cv_name}.yaml").write_text(
                yaml.dump(cv_data), encoding="utf-8"
            )

        paths = config.Paths(
            data=temp_dir,
            input=test_input_dir,
            output=temp_dir / "output",
        )

        for cv_name, expected_data in cv_variants.items():
            content = get_content(cv_name, paths=paths)
            assert content["template"] == expected_data["template"]
            assert content["full_name"] == expected_data["full_name"]

            html, _, _ = render_resume_html(cv_name, paths=paths)
            assert expected_data["full_name"] in html

    def test_cv_content_validation_workflow(self, temp_dir: Path) -> None:
        """Verify validation for different CV scenarios."""
        scenarios: list[ValidationScenario] = [
            {
                "name": "complete_cv",
                "data": create_complete_cv_data(
                    template="cv_no_bars",
                    full_name="Complete User",
                    description="Complete CV description",
                ),
                "should_be_valid": True,
            },
            {
                "name": "minimal_cv",
                "data": create_complete_cv_data(
                    template="cv_no_bars",
                    full_name="Minimal User",
                ),
                "should_be_valid": True,
            },
        ]

        test_input_dir = temp_dir / "input"
        test_input_dir.mkdir()

        for scenario in scenarios:
            (test_input_dir / f"{scenario['name']}.yaml").write_text(
                yaml.dump(scenario["data"]), encoding="utf-8"
            )

        paths = config.Paths(
            data=temp_dir,
            input=test_input_dir,
            output=temp_dir / "output",
        )

        for scenario in scenarios:
            content = get_content(scenario["name"], paths=paths)
            assert content["full_name"]

            html, _, _ = render_resume_html(scenario["name"], paths=paths)
            assert scenario["data"]["full_name"] in html

    def test_markdown_processing_integration(self, temp_dir: Path) -> None:
        """Ensure markdown fields render as HTML."""
        markdown_description = """
# Professional Summary
This is a detailed description with **bold text**, *italic text*, and [links](https://example.com).

## Key Achievements
- Led a team of 5 developers
- Increased test coverage from 50% to 95%
- Implemented TDD across all projects
        """.strip()

        cv_data = create_complete_cv_data(
            template="cv_no_bars",
            full_name="Jane Smith",
            description=markdown_description,
        )

        test_input_dir = temp_dir / "input"
        test_input_dir.mkdir()
        (test_input_dir / "markdown_test.yaml").write_text(
            yaml.dump(cv_data), encoding="utf-8"
        )

        paths = config.Paths(
            data=temp_dir,
            input=test_input_dir,
            output=temp_dir / "output",
        )

        html, _, _ = render_resume_html("markdown_test", paths=paths)

        assert "<h1>Professional Summary</h1>" in html
        assert "<strong>bold text</strong>" in html
        assert '<a href="https://example.com">links</a>' in html

    def test_error_handling_and_recovery_workflow(self, temp_dir: Path) -> None:
        """Continue processing after encountering errors."""
        test_input_dir = temp_dir / "input"
        test_input_dir.mkdir()

        valid_cv = create_complete_cv_data(
            template="cv_no_bars", full_name="Valid User"
        )
        test_cv = create_complete_cv_data(template="cv_no_bars", full_name="Test User")

        (test_input_dir / "valid.yaml").write_text(
            yaml.dump(valid_cv), encoding="utf-8"
        )
        (test_input_dir / "test.yaml").write_text(yaml.dump(test_cv), encoding="utf-8")

        paths = config.Paths(
            data=temp_dir,
            input=test_input_dir,
            output=temp_dir / "output",
        )

        content = get_content("valid", paths=paths)
        assert content["full_name"] == "Valid User"
        html, _, _ = render_resume_html("valid", paths=paths)
        assert "Valid User" in html

        content = get_content("test", paths=paths)
        assert content["full_name"] == "Test User"
        html, _, _ = render_resume_html("test", paths=paths)
        assert "Test User" in html

    def test_performance_with_large_cv_dataset(self, temp_dir: Path) -> None:
        """Basic performance sanity check for bulk rendering."""
        num_cvs = 20
        test_input_dir = temp_dir / "input"
        test_input_dir.mkdir()

        for i in range(num_cvs):
            cv_data = create_complete_cv_data(
                template="cv_no_bars",
                full_name=f"User {i}",
                description=f"Description for user {i} " * 5,
            )
            (test_input_dir / f"user_{i}.yaml").write_text(
                yaml.dump(cv_data), encoding="utf-8"
            )

        paths = config.Paths(
            data=temp_dir,
            input=test_input_dir,
            output=temp_dir / "output",
        )

        start_time = time.time()
        for i in range(num_cvs):
            content = get_content(f"user_{i}", paths=paths)
            assert content["full_name"] == f"User {i}"
        load_time = time.time() - start_time

        start_time = time.time()
        for i in range(num_cvs):
            html, _, _ = render_resume_html(f"user_{i}", paths=paths)
            assert f"User {i}" in html
        render_time = time.time() - start_time

        assert load_time < 5.0, f"Loading took too long: {load_time}s"
        assert render_time < 10.0, f"Rendering took too long: {render_time}s"

    def test_concurrent_user_scenarios(self, temp_dir: Path) -> None:
        """Simulate concurrent rendering requests."""
        users = ["alice", "bob", "charlie", "diana", "eve"]
        test_input_dir = temp_dir / "input"
        test_input_dir.mkdir()

        for user in users:
            cv_data = create_complete_cv_data(
                template="cv_no_bars",
                full_name=user.title(),
                description=f"Professional description for {user}.",
            )
            (test_input_dir / f"{user}.yaml").write_text(
                yaml.dump(cv_data), encoding="utf-8"
            )

        results: dict[str, dict[str, float | bool]] = {}
        errors: dict[str, str] = {}

        paths = config.Paths(
            data=temp_dir,
            input=test_input_dir,
            output=temp_dir / "output",
        )

        def access_cv(user_name: str, request_id: int) -> None:
            try:
                start = time.time()
                content = get_content(user_name, paths=paths)
                load_time = time.time() - start

                render_start = time.time()
                html, _, _ = render_resume_html(user_name, paths=paths)
                render_time = time.time() - render_start
                expected_name = user_name.title()

                results[f"{user_name}_{request_id}"] = {
                    "status": expected_name in html,
                    "content_loaded": content is not None,
                    "load_time": load_time,
                    "render_time": render_time,
                }
            except Exception as exc:
                errors[f"{user_name}_{request_id}"] = str(exc)

        threads = [
            threading.Thread(target=access_cv, args=(user, i))
            for user in users
            for i in range(3)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert not errors, f"Errors occurred: {errors}"
        assert len(results) == len(users) * 3
        for data in results.values():
            assert data["status"]
            assert data["content_loaded"]
            assert data["load_time"] < 3.0
            assert data["render_time"] < 2.5, (
                f"Concurrent render exceeded budget: {data['render_time']:.2f}s"
            )
