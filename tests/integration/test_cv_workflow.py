"""Integration tests for CV generation workflow following extreme programming practices.

These tests follow TDD principles with focus on:
- End-to-end workflow testing
- Real file system interactions
- Integration between components
- Business process validation
- User story scenarios
"""

import threading
import time
from pathlib import Path
from typing import Any, TypedDict
from unittest.mock import patch

import yaml

from cv.index import APP
from cv.utilities import get_content
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
        """GREEN: Test complete workflow from YAML to web rendering."""
        # Arrange - Create realistic CV data
        cv_file = temp_dir / "john_doe.yaml"
        with open(cv_file, "w", encoding="utf-8") as f:
            yaml.dump(sample_cv_data, f)

        # Set up temporary paths for testing
        test_input_dir = temp_dir / "input"
        test_input_dir.mkdir()
        (test_input_dir / "john_doe.yaml").write_text(cv_file.read_text())

        # Act - Test the complete workflow
        with patch("cv.utilities.PATH_INPUT", str(test_input_dir) + "/"):
            # Step 1: Load CV content
            cv_content = get_content("john_doe")

            # Step 2: Verify content structure
            assert "template" in cv_content
            assert "full_name" in cv_content
            assert cv_content["full_name"] == "John Doe"

            # Step 3: Test web rendering
            with APP.test_client() as client:
                response = client.get("/v/john_doe")

            # Assert
            assert response.status_code == 200
            assert b"John Doe" in response.data

    def test_multiple_cv_management_workflow(self, temp_dir: Path) -> None:
        """GREEN: Test workflow with multiple CVs for different purposes."""
        # Arrange - Create multiple CV variants using helper function
        cv_variants = {
            "technical_cv": create_complete_cv_data(
                template="cv_no_bars",
                full_name="Alice Johnson",
                expertise=["Python", "Docker", "Kubernetes", "CI/CD"],
                experience=[
                    {
                        "start": "01/2020",
                        "end": "Present",
                        "title": "Senior DevOps Engineer",
                        "company": "TechCorp",
                        "description": "Managed **containerized** deployments",
                    }
                ],
            ),
            "managerial_cv": create_complete_cv_data(
                template="cv_with_bars",
                full_name="Alice Johnson",
                expertise={
                    "Team Leadership": 90,
                    "Project Management": 85,
                    "Agile": 80,
                },
                experience=[
                    {
                        "start": "01/2018",
                        "end": "Present",
                        "title": "Engineering Manager",
                        "company": "TechCorp",
                        "description": "Led a team of **10 engineers**",
                    }
                ],
            ),
        }

        test_input_dir = temp_dir / "input"
        test_input_dir.mkdir()

        # Create CV files
        for cv_name, cv_data in cv_variants.items():
            cv_file = test_input_dir / f"{cv_name}.yaml"
            with open(cv_file, "w", encoding="utf-8") as f:
                yaml.dump(cv_data, f)

        # Act & Assert - Test each CV variant
        with patch("cv.utilities.PATH_INPUT", str(test_input_dir) + "/"):
            for cv_name, expected_data in cv_variants.items():
                # Load content
                content = get_content(cv_name)

                # Verify content matches expected structure
                assert content["template"] == expected_data["template"]
                assert content["full_name"] == expected_data["full_name"]
                assert len(content["expertise"]) == len(expected_data["expertise"])

                # Test web rendering
                with APP.test_client() as client:
                    response = client.get(f"/v/{cv_name}")
                    assert response.status_code == 200
                    assert expected_data["full_name"].encode() in response.data

    def test_cv_content_validation_workflow(self, temp_dir: Path) -> None:
        """GREEN: Business logic validation for CV content requirements."""
        # Arrange - Test various CV content scenarios
        test_scenarios: list[ValidationScenario] = [
            {
                "name": "complete_cv",
                "data": create_complete_cv_data(
                    template="cv_no_bars",
                    full_name="Complete User",
                    description="Complete CV description",
                    expertise=["Skill1", "Skill2"],
                    experience=[{"title": "Developer", "company": "TechCo"}],
                ),
                "should_be_valid": True,
            },
            {
                "name": "minimal_cv",
                "data": create_complete_cv_data(
                    template="cv_no_bars", full_name="Minimal User"
                ),
                "should_be_valid": True,
            },
        ]

        test_input_dir = temp_dir / "input"
        test_input_dir.mkdir()

        # Act & Assert - Test each scenario
        for scenario in test_scenarios:
            cv_file = test_input_dir / f"{scenario['name']}.yaml"
            with open(cv_file, "w", encoding="utf-8") as f:
                yaml.dump(scenario["data"], f)

            with patch("cv.utilities.PATH_INPUT", str(test_input_dir) + "/"):
                # Should load successfully
                content = get_content(scenario["name"])
                assert content is not None

                # Should render in web interface
                with APP.test_client() as client:
                    response = client.get(f"/v/{scenario['name']}")
                    assert response.status_code == 200

    def test_markdown_processing_integration(self, temp_dir: Path) -> None:
        """GREEN: Test markdown processing in complete workflow."""
        # Arrange - Create CV with markdown content using helper function
        markdown_description = """
# Professional Summary
This is a detailed description with **bold text**, *italic text*, and [links](https://example.com).

## Key Achievements
- Led a team of 5 developers
- Increased test coverage from 50% to 95%
- Implemented TDD across all projects

### Technical Skills
- **Python**: Expert level
- **Testing**: Pytest, unittest, mocking
- **CI/CD**: GitHub Actions, GitLab CI

Visit my [portfolio](https://janesmith.dev) for more examples.
        """.strip()

        markdown_experience = [
            {
                "start": "01/2021",
                "end": "Present",
                "title": "Lead Developer",
                "company": "Tech Corp",
                "description": """
## Responsibilities
- Architecture design and implementation
- **Code review** and mentoring
- Establishing **testing best practices**

### Key Projects
1. **E-commerce Platform**: Built using Django with 100% test coverage
            """.strip(),
            }
        ]

        cv_data = create_complete_cv_data(
            template="cv_no_bars",
            full_name="Jane Smith",
            description=markdown_description,
            experience=markdown_experience,
        )

        test_input_dir = temp_dir / "input"
        test_input_dir.mkdir()

        cv_file = test_input_dir / "markdown_test.yaml"
        with open(cv_file, "w", encoding="utf-8") as f:
            yaml.dump(cv_data, f)

        # Act
        with patch("cv.utilities.PATH_INPUT", str(test_input_dir) + "/"):
            # Load and process markdown
            get_content("markdown_test")

            # Test web rendering with processed markdown
            with APP.test_client() as client:
                response = client.get("/v/markdown_test")

        # Assert
        assert response.status_code == 200
        response_text = response.data.decode()

        # Verify markdown was processed to HTML
        assert "<h1>Professional Summary</h1>" in response_text
        assert "<strong>bold text</strong>" in response_text
        assert "<ul>" in response_text
        assert '<a href="https://janesmith.dev">portfolio</a>' in response_text

    def test_error_handling_and_recovery_workflow(self, temp_dir: Path) -> None:
        """GREEN: Test error handling and recovery in complete workflow."""
        # Arrange
        test_input_dir = temp_dir / "input"
        test_input_dir.mkdir()

        # Create valid and test CVs using helper function
        valid_cv = create_complete_cv_data(
            template="cv_no_bars", full_name="Valid User"
        )
        test_cv = create_complete_cv_data(template="cv_no_bars", full_name="Test User")

        with open(test_input_dir / "valid.yaml", "w") as f:
            yaml.dump(valid_cv, f)
        with open(test_input_dir / "test.yaml", "w") as f:
            yaml.dump(test_cv, f)

        # Act & Assert
        with patch("cv.utilities.PATH_INPUT", str(test_input_dir) + "/"):
            # Valid CV should work
            content = get_content("valid")
            assert content["full_name"] == "Valid User"

            with APP.test_client() as client:
                response = client.get("/v/valid")
                assert response.status_code == 200

            # System should continue working with second CV
            content = get_content("test")
            assert content["full_name"] == "Test User"

            with APP.test_client() as client:
                response = client.get("/v/test")
                assert response.status_code == 200

    def test_performance_with_large_cv_dataset(self, temp_dir: Path) -> None:
        """GREEN: Performance test with large number of CVs."""
        # Arrange - Create many CVs
        num_cvs = 20
        test_input_dir = temp_dir / "input"
        test_input_dir.mkdir()

        for i in range(num_cvs):
            cv_data = create_complete_cv_data(
                template="cv_no_bars",
                full_name=f"User {i}",
                description=f"Description for user {i} " * 10,  # Longer description
                expertise=[f"Skill {j}" for j in range(5)],
                experience=[
                    {
                        "title": f"Job {j}",
                        "company": f"Company {j}",
                        "description": f"Description {j} " * 5,
                    }
                    for j in range(3)
                ],
            )
            cv_file = test_input_dir / f"user_{i}.yaml"
            with open(cv_file, "w", encoding="utf-8") as f:
                yaml.dump(cv_data, f)

        # Act - Test loading and rendering performance
        with patch("cv.utilities.PATH_INPUT", str(test_input_dir) + "/"):
            start_time = time.time()

            # Load all CVs
            for i in range(num_cvs):
                content = get_content(f"user_{i}")
                assert content["full_name"] == f"User {i}"

            load_time = time.time() - start_time

            # Test web rendering performance
            start_time = time.time()
            with APP.test_client() as client:
                for i in range(num_cvs):
                    response = client.get(f"/v/user_{i}")
                    assert response.status_code == 200

            render_time = time.time() - start_time

        # Assert - Performance requirements
        assert load_time < 5.0, f"Loading {num_cvs} CVs took too long: {load_time}s"
        assert (
            render_time < 10.0
        ), f"Rendering {num_cvs} CVs took too long: {render_time}s"

    def test_concurrent_user_scenarios(self, temp_dir: Path) -> None:
        """GREEN: Test concurrent access scenarios (multiple users)."""
        # Arrange - Create CVs for multiple users
        users = ["alice", "bob", "charlie", "diana", "eve"]
        test_input_dir = temp_dir / "input"
        test_input_dir.mkdir()

        for user in users:
            cv_data = create_complete_cv_data(
                template="cv_no_bars",
                full_name=user.title(),
                description=f"Professional description for {user}.",
            )
            cv_file = test_input_dir / f"{user}.yaml"
            with open(cv_file, "w", encoding="utf-8") as f:
                yaml.dump(cv_data, f)

        # Act - Simulate concurrent access
        results = {}
        errors = {}

        def access_cv(user_name: str, request_id: int) -> None:
            try:
                with patch("cv.utilities.PATH_INPUT", str(test_input_dir) + "/"):
                    start_time = time.time()
                    content = get_content(user_name)
                    load_time = time.time() - start_time

                    with (
                        APP.test_client() as client,
                        patch("cv.utilities.PATH_INPUT", str(test_input_dir) + "/"),
                    ):
                        response = client.get(f"/v/{user_name}")
                        render_time = time.time() - start_time

                    results[f"{user_name}_{request_id}"] = {
                        "load_time": load_time,
                        "render_time": render_time,
                        "status_code": response.status_code,
                        "content_loaded": content is not None,
                    }
            except Exception as e:
                errors[f"{user_name}_{request_id}"] = str(e)

        # Create multiple threads for concurrent access
        threads = []
        for user in users:
            for i in range(3):  # 3 concurrent requests per user
                thread = threading.Thread(target=access_cv, args=(user, i))
                threads.append(thread)
                thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Assert
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == len(users) * 3, "Not all requests completed"

        # Verify all requests were successful
        for user_data in results.values():
            assert user_data["status_code"] == 200
            assert user_data["content_loaded"]
            assert user_data["load_time"] < 1.0
            assert user_data["render_time"] < 2.0
