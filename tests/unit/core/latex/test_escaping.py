"""Tests for LaTeX escaping functions."""

from __future__ import annotations

import pytest

from simple_resume.core.latex.escaping import escape_latex, escape_url
from tests.bdd import Scenario


class TestEscapeLatex:
    """Tests for escape_latex function."""

    def test_escape_backslash(self, story: Scenario) -> None:
        """Test escaping backslash character."""
        story.given("a backslash character")
        story.when("escaping for LaTeX")
        assert escape_latex("\\") == r"\textbackslash{}"

    def test_escape_ampersand(self, story: Scenario) -> None:
        """Test escaping ampersand character."""
        story.given("an ampersand character")
        story.when("escaping for LaTeX")
        assert escape_latex("&") == r"\&"

    def test_escape_percent(self, story: Scenario) -> None:
        """Test escaping percent character."""
        story.given("a percent character")
        story.when("escaping for LaTeX")
        assert escape_latex("%") == r"\%"

    def test_escape_dollar(self, story: Scenario) -> None:
        """Test escaping dollar sign."""
        story.given("a dollar sign character")
        story.when("escaping for LaTeX")
        assert escape_latex("$") == r"\$"

    def test_escape_hash(self, story: Scenario) -> None:
        """Test escaping hash/pound character."""
        story.given("a hash/pound character")
        story.when("escaping for LaTeX")
        assert escape_latex("#") == r"\#"

    def test_escape_underscore(self, story: Scenario) -> None:
        """Test escaping underscore character."""
        story.given("an underscore character")
        story.when("escaping for LaTeX")
        assert escape_latex("_") == r"\_"

    def test_escape_curly_braces(self, story: Scenario) -> None:
        """Test escaping curly braces."""
        story.given("curly brace characters")
        story.when("escaping for LaTeX")
        assert escape_latex("{") == r"\{"
        assert escape_latex("}") == r"\}"

    def test_escape_tilde(self, story: Scenario) -> None:
        """Test escaping tilde character."""
        story.given("a tilde character")
        story.when("escaping for LaTeX")
        assert escape_latex("~") == r"\textasciitilde{}"

    def test_escape_caret(self, story: Scenario) -> None:
        """Test escaping caret/circumflex character."""
        story.given("a caret/circumflex character")
        story.when("escaping for LaTeX")
        assert escape_latex("^") == r"\textasciicircum{}"

    def test_escape_all_special_chars(self, story: Scenario) -> None:
        """Test escaping string with all special characters."""
        story.given("a string containing all LaTeX special characters")
        story.when("escaping for LaTeX")
        input_str = r"\&%$#_{} ~^"
        result = escape_latex(input_str)
        assert r"\textbackslash{}" in result
        assert r"\&" in result
        assert r"\%" in result
        assert r"\$" in result
        assert r"\#" in result
        assert r"\_" in result
        assert r"\{" in result
        assert r"\}" in result
        assert r"\textasciitilde{}" in result
        assert r"\textasciicircum{}" in result

    def test_escape_regular_text(self, story: Scenario) -> None:
        """Test that regular text passes through unchanged."""
        story.given("regular text without special characters")
        story.when("escaping for LaTeX")
        assert escape_latex("Hello World") == "Hello World"

    def test_escape_mixed_text(self, story: Scenario) -> None:
        """Test escaping mixed regular and special characters."""
        story.given("text with both regular and special characters")
        story.when("escaping for LaTeX")
        assert escape_latex("Price: $50 & up") == r"Price: \$50 \& up"

    def test_empty_string(self, story: Scenario) -> None:
        """Test escaping empty string."""
        story.given("an empty string")
        story.when("escaping for LaTeX")
        assert escape_latex("") == ""

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ("C++", "C++"),  # Regular text
            ("$100", r"\$100"),  # Dollar sign
            ("50%", r"50\%"),  # Percent
            ("email@example.com", "email@example.com"),  # @ is not special in body
            ("file_name", r"file\_name"),  # Underscore
        ],
    )
    def test_various_inputs(
        self, input_text: str, expected: str, story: Scenario
    ) -> None:
        """Test various common inputs."""
        story.given(f"input text '{input_text}'")
        story.when("escaping for LaTeX")
        assert escape_latex(input_text) == expected


class TestEscapeUrl:
    """Tests for escape_url function."""

    def test_escape_percent_in_url(self, story: Scenario) -> None:
        """Test escaping percent in URL."""
        story.given("a percent character in URL")
        story.when("escaping for URL in LaTeX")
        assert escape_url("%") == r"\%"

    def test_escape_hash_in_url(self, story: Scenario) -> None:
        """Test escaping hash in URL."""
        story.given("a hash character in URL")
        story.when("escaping for URL in LaTeX")
        assert escape_url("#") == r"\#"

    def test_escape_ampersand_in_url(self, story: Scenario) -> None:
        """Test escaping ampersand in URL."""
        story.given("an ampersand character in URL")
        story.when("escaping for URL in LaTeX")
        assert escape_url("&") == r"\&"

    def test_escape_underscore_in_url(self, story: Scenario) -> None:
        """Test escaping underscore in URL."""
        story.given("an underscore character in URL")
        story.when("escaping for URL in LaTeX")
        assert escape_url("_") == r"\_"

    def test_simple_url(self, story: Scenario) -> None:
        """Test simple URL with no special characters."""
        story.given("a simple URL without special characters")
        story.when("escaping for URL in LaTeX")
        url = "https://example.com"
        assert escape_url(url) == url

    def test_url_with_query_params(self, story: Scenario) -> None:
        """Test URL with query parameters."""
        story.given("a URL with query parameters containing ampersands")
        story.when("escaping for URL in LaTeX")
        url = "https://example.com?foo=bar&baz=qux"
        expected = r"https://example.com?foo=bar\&baz=qux"
        assert escape_url(url) == expected

    def test_url_with_anchor(self, story: Scenario) -> None:
        """Test URL with anchor/fragment."""
        story.given("a URL with an anchor/fragment")
        story.when("escaping for URL in LaTeX")
        url = "https://example.com/page#section"
        expected = r"https://example.com/page\#section"
        assert escape_url(url) == expected

    def test_url_with_encoded_chars(self, story: Scenario) -> None:
        """Test URL with percent-encoded characters."""
        story.given("a URL with percent-encoded spaces")
        story.when("escaping for URL in LaTeX")
        url = "https://example.com/path%20with%20spaces"
        expected = r"https://example.com/path\%20with\%20spaces"
        assert escape_url(url) == expected

    def test_github_url_with_underscore(self, story: Scenario) -> None:
        """Test GitHub URL with underscore in username."""
        story.given("a GitHub URL with underscores in username and repo")
        story.when("escaping for URL in LaTeX")
        url = "https://github.com/user_name/repo_name"
        expected = r"https://github.com/user\_name/repo\_name"
        assert escape_url(url) == expected

    def test_complex_url(self, story: Scenario) -> None:
        """Test complex URL with multiple special characters."""
        story.given("a complex URL with multiple special characters")
        story.when("escaping for URL in LaTeX")
        url = "https://site.com/path?q=test&id=123#top_section"
        expected = r"https://site.com/path?q=test\&id=123\#top\_section"
        assert escape_url(url) == expected

    def test_empty_url(self, story: Scenario) -> None:
        """Test empty URL."""
        story.given("an empty URL string")
        story.when("escaping for URL in LaTeX")
        assert escape_url("") == ""

    def test_url_escaping_subset_of_latex(self, story: Scenario) -> None:
        """Test that URL escaping is more limited than LaTeX escaping."""
        story.given("characters that are special in LaTeX but not URLs")
        story.when("escaping for URL in LaTeX")
        # Dollar sign should not be escaped in URLs
        assert escape_url("$") == "$"
        # Curly braces should not be escaped in URLs
        assert escape_url("{") == "{"
        assert escape_url("}") == "}"

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("http://example.com", "http://example.com"),
            ("mailto:user@example.com", "mailto:user@example.com"),
            ("https://site.com#anchor", r"https://site.com\#anchor"),
            ("file:///path/to/file", "file:///path/to/file"),
        ],
    )
    def test_various_url_schemes(
        self, url: str, expected: str, story: Scenario
    ) -> None:
        """Test various URL schemes."""
        story.given(f"URL with scheme from '{url}'")
        story.when("escaping for URL in LaTeX")
        assert escape_url(url) == expected
