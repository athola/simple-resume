"""Template rendering tests adhering to Given/When/Then structure."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from bs4 import BeautifulSoup

from simple_resume.rendering import render_resume_html
from tests.bdd import scenario
from tests.conftest import (
    create_complete_resume_data,
    make_resume_with_projects,
)


def _render(name: str) -> BeautifulSoup:
    html, _, _ = render_resume_html(name, preview=True)
    return BeautifulSoup(html, "html.parser")


class TestTemplateStructureChanges:
    """Sidebar placement and optional fields."""

    @patch("simple_resume.rendering.get_content")
    def test_image_fields_remove_profile_markup(self, mock_get_content: Any) -> None:
        story = scenario("exclude legacy profile markup")
        resume_data = create_complete_resume_data(
            template="resume_no_bars", full_name="John Doe"
        )
        resume_data["image_uri"] = "images/profile.jpg"
        resume_data["image_link"] = "https://example.com"
        mock_get_content.return_value = resume_data

        dom = _render("john_doe")

        story.then("no profile container or image is rendered in the sidebar")
        assert dom.find(class_="profile") is None
        assert dom.find("img", src="images/profile.jpg") is None

    @patch("simple_resume.rendering.get_content")
    def test_given_resume_when_rendering_then_sidebar_contains_full_name(
        self, mock_get_content: Any
    ) -> None:
        story = scenario("sidebar shows candidate name")
        resume_data = create_complete_resume_data(
            template="resume_no_bars", full_name="Alice Johnson"
        )
        mock_get_content.return_value = resume_data

        dom = _render("alice_johnson")

        sidebar = dom.find(class_="sidebar")
        story.then("sidebar includes candidate name")
        assert sidebar is not None
        assert "Alice Johnson" in sidebar.text

    @patch("simple_resume.rendering.get_content")
    def test_given_markdown_description_when_rendering_then_sidebar_contains_html(
        self, mock_get_content: Any
    ) -> None:
        resume_data = create_complete_resume_data(
            template="resume_no_bars",
            full_name="Bob Smith",
            description="**Senior Software Engineer** with 10 years experience",
        )
        mock_get_content.return_value = resume_data

        dom = _render("bob_smith")
        sidebar_text = dom.get_text(" ")
        assert "Senior Software Engineer" in sidebar_text

    @patch("simple_resume.rendering.get_content")
    def test_given_all_templates_when_rendering_then_profile_markup_remains_absent(
        self, mock_get_content: Any
    ) -> None:
        for template in ("resume_no_bars", "resume_with_bars"):
            resume_data = create_complete_resume_data(
                template=template, full_name="Test User"
            )
            resume_data["image_uri"] = "images/test.jpg"
            mock_get_content.return_value = resume_data

            dom = _render(f"test_{template}")
            assert dom.find(class_="profile") is None

    @patch("simple_resume.rendering.get_content")
    def test_given_missing_image_fields_when_rendering_then_template_succeeds(
        self, mock_get_content: Any
    ) -> None:
        resume_data = create_complete_resume_data(
            template="resume_no_bars", full_name="Jane Doe"
        )
        resume_data.pop("image_uri", None)
        resume_data.pop("image_link", None)
        mock_get_content.return_value = resume_data

        dom = _render("jane_doe")
        assert dom.find(string="Jane Doe") is not None


class TestProjectsSectionSupport:
    """Project section markup behaviour."""

    @patch("simple_resume.rendering.get_content")
    def test_given_projects_section_when_rendering_then_details_are_present(
        self, mock_get_content: Any
    ) -> None:
        resume_data = make_resume_with_projects(full_name="Dev User")
        mock_get_content.return_value = resume_data

        dom = _render("dev_user")
        text_content = dom.get_text(" ")
        assert "Projects" in text_content
        assert "ML Platform" in text_content
        assert "Side Project" in text_content
        assert dom.find("a", href="https://example.com/ml") is not None

    @patch("simple_resume.rendering.get_content")
    def test_given_project_title_link_when_rendering_then_anchor_is_emitted(
        self, mock_get_content: Any
    ) -> None:
        resume_data = create_complete_resume_data(
            template="resume_no_bars", full_name="Dev User"
        )
        resume_data["body"]["Projects"] = [
            {
                "start": "",
                "end": "2023",
                "title": "ML Recommendation Engine",
                "title_link": "https://github.com/user/ml-engine",
                "company": "Open Source",
                "description": "Built recommendation system with TensorFlow",
            }
        ]
        mock_get_content.return_value = resume_data

        dom = _render("dev_user")
        link = dom.find("a", href="https://github.com/user/ml-engine")
        assert link is not None
        assert link.text.strip() == "ML Recommendation Engine"

    @patch("simple_resume.rendering.get_content")
    def test_given_project_description_when_rendering_then_rich_text_is_preserved(
        self, mock_get_content: Any
    ) -> None:
        resume_data = create_complete_resume_data(
            template="resume_no_bars", full_name="Dev User"
        )
        resume_data["body"]["Projects"] = [
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
        mock_get_content.return_value = resume_data

        dom = _render("dev_user")
        assert dom.find(string=lambda text: text and "Tech Stack" in text)
        assert dom.find(string=lambda text: text and "Python" in text)
