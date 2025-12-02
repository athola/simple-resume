"""Tests for LaTeX formatting functions."""

from __future__ import annotations

import pytest

from simple_resume.core.latex.formatting import format_date, linkify


class TestFormatDate:
    """Tests for format_date function."""

    def test_both_dates_provided(self) -> None:
        """Test with both start and end dates."""
        result = format_date("2020", "2023")
        assert result == "2020 -- 2023"

    def test_same_start_and_end(self) -> None:
        """Test when start and end are the same."""
        result = format_date("2023", "2023")
        assert result == "2023"

    def test_only_start_date(self) -> None:
        """Test with only start date."""
        result = format_date("2020", None)
        assert result == "2020"

    def test_only_end_date(self) -> None:
        """Test with only end date."""
        result = format_date(None, "2023")
        assert result == "2023"

    def test_both_none(self) -> None:
        """Test with both dates as None."""
        result = format_date(None, None)
        assert result is None

    def test_empty_strings(self) -> None:
        """Test with empty strings."""
        result = format_date("", "")
        assert result is None

    def test_start_empty_end_provided(self) -> None:
        """Test with empty start and provided end."""
        result = format_date("", "2023")
        assert result == "2023"

    def test_start_provided_end_empty(self) -> None:
        """Test with provided start and empty end."""
        result = format_date("2020", "")
        assert result == "2020"

    def test_whitespace_handling(self) -> None:
        """Test that whitespace is stripped."""
        result = format_date("  2020  ", "  2023  ")
        assert result == "2020 -- 2023"

    def test_date_range_with_months(self) -> None:
        """Test with month-year format."""
        result = format_date("Jan 2020", "Dec 2023")
        assert result == "Jan 2020 -- Dec 2023"

    def test_present_as_end_date(self) -> None:
        """Test with 'Present' as end date."""
        result = format_date("2020", "Present")
        assert result == "2020 -- Present"

    def test_markdown_in_dates(self) -> None:
        """Test that markdown is converted in dates."""
        result = format_date("**2020**", "*Present*")
        assert result is not None
        assert r"\textbf{2020}" in result
        assert r"\textit{Present}" in result

    def test_special_chars_in_dates(self) -> None:
        """Test that special LaTeX chars are escaped in dates."""
        result = format_date("2020 (Q1)", "2023 & beyond")
        assert result is not None
        assert r"\&" in result

    @pytest.mark.parametrize(
        "start,end,expected",
        [
            ("2020", "2023", "2020 -- 2023"),
            ("2023", "2023", "2023"),
            ("2020", None, "2020"),
            (None, "2023", "2023"),
            (None, None, None),
            ("", "", None),
            ("Jan 2020", "Present", "Jan 2020 -- Present"),
        ],
    )
    def test_various_date_combinations(
        self, start: str | None, end: str | None, expected: str | None
    ) -> None:
        """Test various date combinations."""
        assert format_date(start, end) == expected


class TestLinkify:
    """Tests for linkify function."""

    def test_text_without_link(self) -> None:
        """Test text without a link URL."""
        result = linkify("Company Name", None)
        assert result == "Company Name"

    def test_text_with_link(self) -> None:
        """Test text with a link URL."""
        result = linkify("Company Name", "https://example.com")
        assert result is not None
        assert r"\href{https://example.com}{Company Name}" in result

    def test_none_text(self) -> None:
        """Test with None text."""
        result = linkify(None, "https://example.com")
        assert result is None

    def test_empty_text(self) -> None:
        """Test with empty text."""
        result = linkify("", "https://example.com")
        assert result is None

    def test_none_link(self) -> None:
        """Test with None link."""
        result = linkify("Text", None)
        assert result == "Text"

    def test_empty_link(self) -> None:
        """Test with empty link (treated as None)."""
        result = linkify("Text", "")
        assert result == "Text"

    def test_markdown_in_text(self) -> None:
        """Test that markdown is converted in text."""
        result = linkify("**Bold Company**", None)
        assert result is not None
        assert r"\textbf{Bold Company}" in result

    def test_markdown_in_text_with_link(self) -> None:
        """Test markdown conversion with link."""
        result = linkify("*Company Name*", "https://example.com")
        assert result is not None
        assert r"\href{" in result
        assert r"\textit{Company Name}" in result

    def test_special_chars_in_url(self) -> None:
        """Test that special chars are escaped in URL."""
        result = linkify("Search", "https://example.com?q=test&foo=bar#section")
        assert result is not None
        assert r"\href{https://example.com?q=test\&foo=bar\#section}" in result

    def test_special_chars_in_text(self) -> None:
        """Test that special chars are escaped in text."""
        result = linkify("C++ Developer", None)
        assert result is not None
        assert "C++" in result

    def test_complex_url(self) -> None:
        """Test with complex URL."""
        result = linkify(
            "GitHub Profile",
            "https://github.com/user_name/repo#readme",
        )
        assert result is not None
        assert r"\href{https://github.com/user\_name/repo\#readme}" in result

    def test_both_text_and_link_none(self) -> None:
        """Test with both text and link as None."""
        result = linkify(None, None)
        assert result is None

    @pytest.mark.parametrize(
        "text,link,expected_contains",
        [
            ("Text", None, "Text"),
            ("Text", "", "Text"),
            (None, "http://example.com", None),
            ("", "http://example.com", None),
            ("Link", "http://example.com", r"\href{http://example.com}{Link}"),
        ],
    )
    def test_various_combinations(
        self, text: str | None, link: str | None, expected_contains: str | None
    ) -> None:
        """Test various text and link combinations."""
        result = linkify(text, link)
        if expected_contains is None:
            assert result is None
        else:
            assert result is not None
            assert expected_contains in result
