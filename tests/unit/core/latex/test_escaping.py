"""Tests for LaTeX escaping functions."""

from __future__ import annotations

import pytest

from simple_resume.core.latex.escaping import escape_latex, escape_url


class TestEscapeLatex:
    """Tests for escape_latex function."""

    def test_escape_backslash(self) -> None:
        """Test escaping backslash character."""
        assert escape_latex("\\") == r"\textbackslash{}"

    def test_escape_ampersand(self) -> None:
        """Test escaping ampersand character."""
        assert escape_latex("&") == r"\&"

    def test_escape_percent(self) -> None:
        """Test escaping percent character."""
        assert escape_latex("%") == r"\%"

    def test_escape_dollar(self) -> None:
        """Test escaping dollar sign."""
        assert escape_latex("$") == r"\$"

    def test_escape_hash(self) -> None:
        """Test escaping hash/pound character."""
        assert escape_latex("#") == r"\#"

    def test_escape_underscore(self) -> None:
        """Test escaping underscore character."""
        assert escape_latex("_") == r"\_"

    def test_escape_curly_braces(self) -> None:
        """Test escaping curly braces."""
        assert escape_latex("{") == r"\{"
        assert escape_latex("}") == r"\}"

    def test_escape_tilde(self) -> None:
        """Test escaping tilde character."""
        assert escape_latex("~") == r"\textasciitilde{}"

    def test_escape_caret(self) -> None:
        """Test escaping caret/circumflex character."""
        assert escape_latex("^") == r"\textasciicircum{}"

    def test_escape_all_special_chars(self) -> None:
        """Test escaping string with all special characters."""
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

    def test_escape_regular_text(self) -> None:
        """Test that regular text passes through unchanged."""
        assert escape_latex("Hello World") == "Hello World"

    def test_escape_mixed_text(self) -> None:
        """Test escaping mixed regular and special characters."""
        assert escape_latex("Price: $50 & up") == r"Price: \$50 \& up"

    def test_empty_string(self) -> None:
        """Test escaping empty string."""
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
    def test_various_inputs(self, input_text: str, expected: str) -> None:
        """Test various common inputs."""
        assert escape_latex(input_text) == expected


class TestEscapeUrl:
    """Tests for escape_url function."""

    def test_escape_percent_in_url(self) -> None:
        """Test escaping percent in URL."""
        assert escape_url("%") == r"\%"

    def test_escape_hash_in_url(self) -> None:
        """Test escaping hash in URL."""
        assert escape_url("#") == r"\#"

    def test_escape_ampersand_in_url(self) -> None:
        """Test escaping ampersand in URL."""
        assert escape_url("&") == r"\&"

    def test_escape_underscore_in_url(self) -> None:
        """Test escaping underscore in URL."""
        assert escape_url("_") == r"\_"

    def test_simple_url(self) -> None:
        """Test simple URL with no special characters."""
        url = "https://example.com"
        assert escape_url(url) == url

    def test_url_with_query_params(self) -> None:
        """Test URL with query parameters."""
        url = "https://example.com?foo=bar&baz=qux"
        expected = r"https://example.com?foo=bar\&baz=qux"
        assert escape_url(url) == expected

    def test_url_with_anchor(self) -> None:
        """Test URL with anchor/fragment."""
        url = "https://example.com/page#section"
        expected = r"https://example.com/page\#section"
        assert escape_url(url) == expected

    def test_url_with_encoded_chars(self) -> None:
        """Test URL with percent-encoded characters."""
        url = "https://example.com/path%20with%20spaces"
        expected = r"https://example.com/path\%20with\%20spaces"
        assert escape_url(url) == expected

    def test_github_url_with_underscore(self) -> None:
        """Test GitHub URL with underscore in username."""
        url = "https://github.com/user_name/repo_name"
        expected = r"https://github.com/user\_name/repo\_name"
        assert escape_url(url) == expected

    def test_complex_url(self) -> None:
        """Test complex URL with multiple special characters."""
        url = "https://site.com/path?q=test&id=123#top_section"
        expected = r"https://site.com/path?q=test\&id=123\#top\_section"
        assert escape_url(url) == expected

    def test_empty_url(self) -> None:
        """Test empty URL."""
        assert escape_url("") == ""

    def test_url_escaping_subset_of_latex(self) -> None:
        """Test that URL escaping is more limited than LaTeX escaping."""
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
    def test_various_url_schemes(self, url: str, expected: str) -> None:
        """Test various URL schemes."""
        assert escape_url(url) == expected
