"""Integration tests for Resume generation without a web server."""

from __future__ import annotations

import tempfile
import threading
import time
from pathlib import Path
from typing import Any, TypedDict

import pytest
import yaml
from bs4 import BeautifulSoup

from simple_resume.core.effects import Effect
from simple_resume.core.generate.exceptions import TemplateError
from simple_resume.core.generate.html import create_html_generator_factory
from simple_resume.core.paths import Paths
from simple_resume.core.result import GenerationMetadata
from simple_resume.core.resume import Resume
from simple_resume.shell.runtime.content import get_content
from simple_resume.shell.services import DefaultTemplateLocator
from tests.bdd import scenario
from tests.conftest import create_complete_resume_data


class ValidationScenario(TypedDict):
    """Typed scenario definition for Resume validation tests."""

    name: str
    data: dict[str, Any]
    should_be_valid: bool


def _build_paths(base: Path) -> Paths:
    """Construct paths structure for tests using temporary directories."""
    input_dir = base / "input"
    output_dir = base / "output"
    content_dir = base / "content"
    templates_dir = base / "templates"
    static_dir = base / "static"
    for directory in (input_dir, output_dir, content_dir, templates_dir, static_dir):
        directory.mkdir(parents=True, exist_ok=True)
    return Paths(
        data=base,
        input=input_dir,
        output=output_dir,
        content=content_dir,
        templates=templates_dir,
        static=static_dir,
    )


def render_resume_html(
    name: str, paths: Paths, *, preview: bool = False
) -> tuple[str, list[Effect], GenerationMetadata]:
    """Render HTML by building a plan from hydrated resume data."""
    resume_data = get_content(name, paths=paths)
    resume = Resume.from_data(resume_data, name=name, paths=paths)
    render_plan = resume.prepare_render_plan(preview=preview)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    template_locator = DefaultTemplateLocator()
    factory = create_html_generator_factory(default_template_locator=template_locator)
    prepare_html_func = factory.create_prepare_html_function()
    return prepare_html_func(
        render_plan,
        tmp_path,
        resume_name=name,
        template_locator=template_locator,
    )


class TestResumeWorkflowIntegration:
    """Integration tests for complete Resume generation workflow."""

    def test_end_to_end_resume_creation_workflow(
        self, temp_dir: Path, sample_resume_data: dict[str, Any]
    ) -> None:
        """Validate loading YAML and rendering HTML."""
        story = scenario("end-to-end resume creation")
        story.given("a YAML resume stored in the input directory")

        resume_file = temp_dir / "john_doe.yaml"
        resume_file.write_text(yaml.dump(sample_resume_data), encoding="utf-8")

        paths = _build_paths(temp_dir)
        (paths.input / "john_doe.yaml").write_text(
            resume_file.read_text(encoding="utf-8"), encoding="utf-8"
        )

        story.when("the resume content is hydrated and rendered to HTML")
        resume_content = get_content("john_doe", paths=paths)
        html, _, _ = render_resume_html("john_doe", paths=paths)

        story.then("the hydrated content preserves metadata")
        assert resume_content["full_name"] == "John Doe"

        story.then("the rendered HTML includes semantic sections")
        soup = BeautifulSoup(html, "html.parser")
        header = soup.find("h1")
        assert header and header.text.strip() == "John Doe"
        assert soup.find(string="Contact"), "Contact section missing from HTML"

    def test_multiple_resume_management_workflow(self, temp_dir: Path) -> None:
        """Handle multiple Resume variants in a single directory."""
        story = scenario("manage multiple resume variants")
        story.given(
            "technical and managerial resume inputs placed in the input directory"
        )

        resume_variants = {
            "technical_resume": create_complete_resume_data(
                template="resume_no_bars",
                full_name="Alice Johnson",
                expertise=["Python", "Docker", "Kubernetes", "CI/CD"],
            ),
            "managerial_resume": create_complete_resume_data(
                template="resume_with_bars",
                full_name="Alice Johnson",
                expertise={
                    "Team Leadership": 90,
                    "Project Management": 85,
                    "Agile": 80,
                },
            ),
        }

        paths = _build_paths(temp_dir)
        for resume_name, resume_data in resume_variants.items():
            (paths.input / f"{resume_name}.yaml").write_text(
                yaml.dump(resume_data), encoding="utf-8"
            )

        story.when("each resume is hydrated and rendered")
        for resume_name, expected_data in resume_variants.items():
            content = get_content(resume_name, paths=paths)
            html, _, _ = render_resume_html(resume_name, paths=paths)

            story.then("the hydrated content matches the source data")
            assert content["template"] == expected_data["template"]
            assert content["full_name"] == expected_data["full_name"]

            story.then("rendered HTML contains key headings for the resume")
            soup = BeautifulSoup(html, "html.parser")
            assert soup.find(string=expected_data["full_name"]) is not None
            assert soup.find_all("h2"), "Expected headings in HTML output"

    def test_resume_content_validation_workflow(self, temp_dir: Path) -> None:
        """Verify validation for different Resume scenarios."""
        story = scenario("validate multiple resume scenarios")
        story.given("complete and minimal resume payloads written to disk")

        scenarios: list[ValidationScenario] = [
            {
                "name": "complete_resume",
                "data": create_complete_resume_data(
                    template="resume_no_bars",
                    full_name="Complete User",
                    description="Complete Resume description",
                ),
                "should_be_valid": True,
            },
            {
                "name": "minimal_resume",
                "data": create_complete_resume_data(
                    template="resume_no_bars",
                    full_name="Minimal User",
                ),
                "should_be_valid": True,
            },
        ]

        paths = _build_paths(temp_dir)
        for case in scenarios:
            (paths.input / f"{case['name']}.yaml").write_text(
                yaml.dump(case["data"]), encoding="utf-8"
            )

        story.when("each scenario is hydrated and rendered")
        for scenario_case in scenarios:
            content = get_content(scenario_case["name"], paths=paths)
            assert content["full_name"], "full_name should be present after hydration"

            html, _, _ = render_resume_html(scenario_case["name"], paths=paths)
            soup = BeautifulSoup(html, "html.parser")
            assert soup.find(string=scenario_case["data"]["full_name"]) is not None

        story.then("all scenarios render without validation errors")

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

        resume_data = create_complete_resume_data(
            template="resume_no_bars",
            full_name="Jane Smith",
            description=markdown_description,
        )

        paths = _build_paths(temp_dir)
        (paths.input / "markdown_test.yaml").write_text(
            yaml.dump(resume_data), encoding="utf-8"
        )

        story = scenario("markdown fields render to HTML")
        story.given("a resume whose description and body contain markdown")

        html, _, _ = render_resume_html("markdown_test", paths=paths)
        soup = BeautifulSoup(html, "html.parser")

        story.then("markdown headings and emphasis are converted to semantic HTML")

        # Returns a BeautifulSoup tag or None
        def _find_tag_with_text(tag_name: str, expected_text: str) -> object | None:
            for element in soup.find_all(tag_name):
                if element.get_text(strip=True) == expected_text:
                    return element
            return None

        heading = _find_tag_with_text("h1", "Professional Summary")
        assert heading is not None
        emphasis = _find_tag_with_text("strong", "bold text")
        assert emphasis is not None
        link = _find_tag_with_text("a", "links")
        assert link is not None
        assert link.get("href") == "https://example.com"  # type: ignore[attr-defined]

    def test_error_handling_and_recovery_workflow(self, temp_dir: Path) -> None:
        """Continue processing after encountering errors."""
        story = scenario("error handling when processing multiple resumes")
        story.given("a directory with one valid resume and one malformed YAML file")

        paths = _build_paths(temp_dir)

        valid_resume = create_complete_resume_data(
            template="resume_no_bars", full_name="Valid User"
        )
        malformed_yaml = "invalid: [unterminated"

        (paths.input / "valid.yaml").write_text(
            yaml.dump(valid_resume), encoding="utf-8"
        )
        (paths.input / "broken.yaml").write_text(malformed_yaml, encoding="utf-8")

        story.when("content is requested for the valid resume and broken resume")
        valid_content = get_content("valid", paths=paths)
        with pytest.raises(yaml.YAMLError):
            get_content("broken", paths=paths)

        story.then("valid resume still hydrates correctly despite neighbour failures")
        assert valid_content["full_name"] == "Valid User"

    def test_missing_template_yields_error(self, temp_dir: Path) -> None:
        """Ensure the workflow surfaces errors when a template cannot be found."""

        story = scenario("missing template failure")
        story.given("resume references a non-existent template")

        resume_data = create_complete_resume_data(template="missing_template")
        paths = _build_paths(temp_dir)
        (paths.input / "missing.yaml").write_text(
            yaml.dump(resume_data), encoding="utf-8"
        )

        story.when("render_resume_html is invoked")
        with pytest.raises(TemplateError) as exc:
            render_resume_html("missing", paths=paths)

        story.then("the error message references the missing template")
        assert exc.value.template_name is not None
        assert "missing_template" in exc.value.template_name

    def test_performance_with_large_resume_dataset(self, temp_dir: Path) -> None:
        """Basic performance sanity check for bulk rendering."""
        story = scenario("bulk rendering performance")
        num_resumes = 20
        paths = _build_paths(temp_dir)

        for i in range(num_resumes):
            resume_data = create_complete_resume_data(
                template="resume_no_bars",
                full_name=f"User {i}",
                description=f"Description for user {i} " * 5,
            )
            (paths.input / f"user_{i}.yaml").write_text(
                yaml.dump(resume_data), encoding="utf-8"
            )

        story.when("loading and rendering a batch of resumes")
        start_time = time.time()
        for i in range(num_resumes):
            content = get_content(f"user_{i}", paths=paths)
            assert content["full_name"] == f"User {i}"
        load_time = time.time() - start_time

        start_time = time.time()
        for i in range(num_resumes):
            html, _, _ = render_resume_html(f"user_{i}", paths=paths)
            assert f"User {i}" in html
        render_time = time.time() - start_time

        story.then("loading and rendering stay within expected timing budgets")
        assert load_time < 5.0, f"Loading took too long: {load_time}s"
        assert render_time < 10.0, f"Rendering took too long: {render_time}s"

    def test_concurrent_user_scenarios(self, temp_dir: Path) -> None:
        """Simulate concurrent rendering requests."""
        story = scenario("concurrent resume rendering")
        users = ["alice", "bob", "charlie", "diana", "eve"]
        paths = _build_paths(temp_dir)

        for user in users:
            resume_data = create_complete_resume_data(
                template="resume_no_bars",
                full_name=user.title(),
                description=f"Professional description for {user}.",
            )
            (paths.input / f"{user}.yaml").write_text(
                yaml.dump(resume_data), encoding="utf-8"
            )

        results: dict[str, dict[str, float | bool]] = {}
        errors: dict[str, str] = {}

        # Reuse paths created earlier

        def access_resume(user_name: str, request_id: int) -> None:
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
            threading.Thread(target=access_resume, args=(user, i))
            for user in users
            for i in range(3)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        story.then("no rendering errors occur and latency stays bounded")
        assert not errors, f"Errors occurred: {errors}"
        assert len(results) == len(users) * 3
        for data in results.values():
            assert data["status"]
            assert data["content_loaded"]
            assert data["load_time"] < 10.0
            assert data["render_time"] < 10.0, (
                f"Concurrent render exceeded budget: {data['render_time']:.2f}s"
            )
