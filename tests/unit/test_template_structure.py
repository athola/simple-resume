"""Template rendering tests without relying on a web server."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from easyresume.rendering import render_resume_html
from tests.conftest import create_complete_cv_data


def _render(name: str) -> str:
    html, _, _ = render_resume_html(name, preview=True)
    return html


class TestTemplateStructureChanges:
    """Sidebar placement and optional fields."""

    @patch("easyresume.rendering.get_content")
    def test_template_renders_without_profile_photo_section(
        self, mock_get_content: Any
    ) -> None:
        """Ensure legacy profile image markup stays removed."""
        cv_data = create_complete_cv_data(template="cv_no_bars", full_name="John Doe")
        cv_data["image_uri"] = "images/profile.jpg"
        cv_data["image_link"] = "https://example.com"
        mock_get_content.return_value = cv_data

        html = _render("john_doe")
        assert 'class="profile"' not in html
        assert "images/profile.jpg" not in html

    @patch("easyresume.rendering.get_content")
    def test_template_renders_name_in_sidebar(self, mock_get_content: Any) -> None:
        """Sidebar should include the full name heading."""
        cv_data = create_complete_cv_data(
            template="cv_no_bars", full_name="Alice Johnson"
        )
        mock_get_content.return_value = cv_data

        html = _render("alice_johnson")
        assert "Alice Johnson" in html
        assert "sidebar" in html.lower()

    @patch("easyresume.rendering.get_content")
    def test_template_renders_description_in_sidebar(
        self, mock_get_content: Any
    ) -> None:
        """Markdown description renders as HTML in the sidebar."""
        cv_data = create_complete_cv_data(
            template="cv_no_bars",
            full_name="Bob Smith",
            description="**Senior Software Engineer** with 10 years experience",
        )
        mock_get_content.return_value = cv_data

        html = _render("bob_smith")
        assert "Senior Software Engineer" in html

    @patch("easyresume.rendering.get_content")
    def test_both_templates_support_photo_removal(self, mock_get_content: Any) -> None:
        """Both templates ignore `image_uri` after removal."""
        templates = ["cv_no_bars", "cv_with_bars"]

        for template in templates:
            cv_data = create_complete_cv_data(template=template, full_name="Test User")
            cv_data["image_uri"] = "images/test.jpg"
            mock_get_content.return_value = cv_data

            html = _render(f"test_{template}")
            assert 'class="profile"' not in html

    @patch("easyresume.rendering.get_content")
    def test_template_works_without_image_fields(self, mock_get_content: Any) -> None:
        """Template renders even when image fields are absent."""
        cv_data = create_complete_cv_data(template="cv_no_bars", full_name="Jane Doe")
        cv_data.pop("image_uri", None)
        cv_data.pop("image_link", None)
        mock_get_content.return_value = cv_data

        html = _render("jane_doe")
        assert "Jane Doe" in html


class TestProjectsSectionSupport:
    """Project section markup behaviour."""

    @patch("easyresume.rendering.get_content")
    def test_template_supports_projects_section(self, mock_get_content: Any) -> None:
        """Projects section displays the expected project details."""
        cv_data = create_complete_cv_data(template="cv_no_bars", full_name="Dev User")
        cv_data["body"]["Projects"] = [
            {
                "start": "",
                "end": "2024",
                "title": "Real-Time Data Pipeline",
                "title_link": "https://github.com/user/project",
                "company": "Personal Project",
                "company_link": "https://github.com/user",
                "description": (
                    "Developed a scalable pipeline processing 500K events/second.\n\n"
                    "- Built with Apache Kafka and Spark\n"
                    "- **Tech Stack:** Python, Kafka, Docker"
                ),
            }
        ]
        mock_get_content.return_value = cv_data

        html = _render("dev_user")
        assert "Projects" in html
        assert "Real-Time Data Pipeline" in html
        assert "Personal Project" in html

    @patch("easyresume.rendering.get_content")
    def test_projects_section_renders_github_links(self, mock_get_content: Any) -> None:
        """Project title links render as anchor tags."""
        cv_data = create_complete_cv_data(template="cv_no_bars", full_name="Dev User")
        cv_data["body"]["Projects"] = [
            {
                "start": "",
                "end": "2023",
                "title": "ML Recommendation Engine",
                "title_link": "https://github.com/user/ml-engine",
                "company": "Open Source",
                "description": "Built recommendation system with TensorFlow",
            }
        ]
        mock_get_content.return_value = cv_data

        html = _render("dev_user")
        assert "github.com/user/ml-engine" in html
        assert "ML Recommendation Engine" in html

    @patch("easyresume.rendering.get_content")
    def test_projects_section_with_tech_stack_highlighting(
        self, mock_get_content: Any
    ) -> None:
        """Tech stack text appears when embedded in descriptions."""
        cv_data = create_complete_cv_data(template="cv_no_bars", full_name="Dev User")
        cv_data["body"]["Projects"] = [
            {
                "start": "",
                "end": "2024",
                "title": "E-commerce Platform",
                "company": "Freelance",
                "description": (
                    "Built full-stack platform with 10K+ users. "
                    "Tech Stack includes Python, Django, React"
                ),
            }
        ]
        mock_get_content.return_value = cv_data

        html = _render("dev_user")
        assert "E-commerce Platform" in html
        assert "Tech Stack" in html
        assert "Python" in html

    @patch("easyresume.rendering.get_content")
    def test_multiple_projects_render_correctly(self, mock_get_content: Any) -> None:
        """All provided projects render in the body."""
        cv_data = create_complete_cv_data(template="cv_no_bars", full_name="Dev User")
        cv_data["body"]["Projects"] = [
            {
                "start": "",
                "end": "2024",
                "title": "Project Alpha",
                "company": "Personal",
                "description": "First project description",
            },
            {
                "start": "",
                "end": "2023",
                "title": "Project Beta",
                "company": "Open Source",
                "description": "Second project description",
            },
            {
                "start": "",
                "end": "2022",
                "title": "Project Gamma",
                "company": "Freelance",
                "description": "Third project description",
            },
        ]
        mock_get_content.return_value = cv_data

        html = _render("dev_user")
        assert "Project Alpha" in html
        assert "Project Beta" in html
        assert "Project Gamma" in html

    @patch("easyresume.rendering.get_content")
    def test_projects_section_ordering_in_body(self, mock_get_content: Any) -> None:
        """Projects section order precedes other sections when configured."""
        cv_data = create_complete_cv_data(template="cv_no_bars", full_name="Dev User")
        cv_data["body"] = {
            "Projects": [{"title": "Project Alpha"}],
            "Experience": [{"title": "Job Alpha"}],
        }
        mock_get_content.return_value = cv_data

        html = _render("dev_user")
        sections = html.split("<h2>")
        assert "Projects</h2>" in sections[1]
        assert "Experience</h2>" in html


class TestSidebarLayoutValidation:
    """Sidebar specific checks."""

    @patch("easyresume.rendering.get_content")
    def test_sidebar_contains_name_and_description(self, mock_get_content: Any) -> None:
        """Sidebar includes both name and description text."""
        cv_data = create_complete_cv_data(
            template="cv_no_bars",
            full_name="Alice Johnson",
            description="Professional summary for Alice Johnson.",
        )
        mock_get_content.return_value = cv_data

        html = _render("dev_user")
        assert "Alice Johnson" in html
        assert "Professional summary for Alice Johnson." in html

    @patch("easyresume.rendering.get_content")
    def test_sidebar_layout_without_description(self, mock_get_content: Any) -> None:
        """Sidebar hides description when the field is empty."""
        cv_data = create_complete_cv_data(
            template="cv_no_bars",
            full_name="Alice Johnson",
            description="Professional summary for Alice Johnson.",
        )
        cv_data["description"] = ""
        mock_get_content.return_value = cv_data

        html = _render("dev_user")
        assert "Professional summary for Alice Johnson." not in html

    @patch("easyresume.rendering.get_content")
    def test_sidebar_preserves_contact_section(self, mock_get_content: Any) -> None:
        """Sidebar retains contact details such as email."""
        cv_data = create_complete_cv_data(
            template="cv_no_bars",
            full_name="Alice Johnson",
        )
        cv_data["email"] = "alice@example.com"
        mock_get_content.return_value = cv_data

        html = _render("dev_user")
        assert "alice@example.com" in html


class TestBackwardCompatibility:
    """Ensure templates still support legacy fields."""

    @patch("easyresume.rendering.get_content")
    def test_cv_without_projects_section_still_works(
        self, mock_get_content: Any
    ) -> None:
        """Template renders when Projects section is removed."""
        cv_data = create_complete_cv_data(template="cv_no_bars", full_name="Test User")
        cv_data["body"].pop("Projects", None)
        mock_get_content.return_value = cv_data

        html = _render("test_user")
        assert "Test User" in html

    @patch("easyresume.rendering.get_content")
    def test_all_body_sections_render_dynamically(self, mock_get_content: Any) -> None:
        """All provided body sections appear in the rendered HTML."""
        cv_data = create_complete_cv_data(template="cv_no_bars", full_name="Test User")
        cv_data["body"] = {
            "Experience": [{"title": "Developer"}],
            "Education": [{"title": "BSc Computer Science"}],
            "Awards": [{"title": "Best Engineer"}],
        }
        mock_get_content.return_value = cv_data

        html = _render("test_user")
        assert "Experience" in html
        assert "Education" in html
        assert "Awards" in html
