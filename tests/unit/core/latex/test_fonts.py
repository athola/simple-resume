"""Tests for LaTeX font support functions."""

from __future__ import annotations

import pytest

from simple_resume.core.latex.fonts import fontawesome_support_block


class TestFontawesomeSupportBlock:
    """Tests for fontawesome_support_block function."""

    def test_fallback_without_directory(self) -> None:
        """Test fallback block when no directory is provided."""
        result = fontawesome_support_block(None)

        # Should contain fallback definitions
        assert r"\IfFileExists{fontawesome.sty}" in result
        assert r"\usepackage{fontawesome}" in result
        assert r"\newcommand{\faPhone}" in result
        assert r"\newcommand{\faEnvelope}" in result
        assert r"\newcommand{\faLinkedin}" in result
        assert r"\newcommand{\faGlobe}" in result
        assert r"\newcommand{\faGithub}" in result
        assert r"\newcommand{\faLocation}" in result

    def test_fallback_with_empty_string(self) -> None:
        """Test fallback when empty string is provided."""
        result = fontawesome_support_block("")

        # Empty string should be treated same as None
        assert r"\IfFileExists{fontawesome.sty}" in result

    def test_fontspec_with_directory(self) -> None:
        """Test fontspec block when directory is provided."""
        result = fontawesome_support_block("/path/to/fonts/")

        # Should contain fontspec definitions
        assert r"\usepackage{fontspec}" in result
        assert r"\newfontfamily\FAFreeSolid" in result
        assert r"\newfontfamily\FAFreeBrands" in result
        assert r"Path=/path/to/fonts/" in result

    def test_font_file_references(self) -> None:
        """Test that correct font files are referenced."""
        result = fontawesome_support_block("/fonts/")

        assert "Font Awesome 6 Free-Solid-900.otf" in result
        assert "Font Awesome 6 Brands-Regular-400.otf" in result

    def test_iftex_conditional(self) -> None:
        """Test that iftex conditional is used."""
        result = fontawesome_support_block("/fonts/")

        assert r"\usepackage{iftex}" in result
        assert r"\ifPDFTeX" in result
        assert r"\else" in result
        assert r"\fi" in result

    def test_icon_definitions_in_fallback(self) -> None:
        """Test that all icons are defined in fallback."""
        result = fontawesome_support_block(None)

        # All icons should have definitions
        icons = [
            "faPhone",
            "faEnvelope",
            "faLinkedin",
            "faGlobe",
            "faGithub",
            "faLocation",
        ]
        for icon in icons:
            assert icon in result

    def test_icon_unicode_in_fontspec(self) -> None:
        """Test that icons use unicode symbols in fontspec."""
        result = fontawesome_support_block("/fonts/")

        # Should use unicode symbols
        assert r'\symbol{"F095}' in result  # phone
        assert r'\symbol{"F0E0}' in result  # envelope
        assert r'\symbol{"F08C}' in result  # linkedin
        assert r'\symbol{"F0AC}' in result  # globe
        assert r'\symbol{"F09B}' in result  # github
        assert r'\symbol{"F3C5}' in result  # location

    def test_falocation_mapping(self) -> None:
        """Test that faLocation is mapped to faMapMarker in fallback."""
        result = fontawesome_support_block(None)

        assert r"\providecommand{\faLocation}{\faMapMarker}" in result

    def test_font_scale(self) -> None:
        """Test that font scale is set."""
        result = fontawesome_support_block("/fonts/")

        assert "Scale=0.72" in result

    def test_indentation_in_conditional(self) -> None:
        """Test proper indentation in ifPDFTeX blocks."""
        result = fontawesome_support_block("/fonts/")

        # Lines inside conditional should be indented
        lines = result.split("\n")

        # Find the lines between \ifPDFTeX and \else
        in_if_block = False
        for line in lines:
            if r"\ifPDFTeX" in line:
                in_if_block = True
                continue
            if r"\else" in line:
                in_if_block = False
                continue

            # Lines in the if block should start with spaces (indented)
            if in_if_block and line.strip():
                assert line.startswith("  "), f"Line should be indented: {line}"

    def test_fallback_text_commands(self) -> None:
        """Test that fallback uses text-based icons."""
        result = fontawesome_support_block(None)

        # Fallback should use simple text replacements
        assert r"\textbf{P}" in result  # Phone
        assert r"\textbf{@}" in result  # Email
        assert r"\textbf{in}" in result  # LinkedIn
        assert r"\textbf{W}" in result  # Web
        assert r"\textbf{GH}" in result  # GitHub
        assert r"\textbf{A}" in result  # Address/Location

    def test_pure_function_no_side_effects(self) -> None:
        """Test that function is pure (same input = same output)."""
        result1 = fontawesome_support_block("/fonts/")
        result2 = fontawesome_support_block("/fonts/")

        assert result1 == result2

    def test_none_and_empty_equivalent(self) -> None:
        """Test that None and empty string produce same result."""
        result_none = fontawesome_support_block(None)
        result_empty = fontawesome_support_block("")

        assert result_none == result_empty

    @pytest.mark.parametrize(
        "font_dir,expected_fragment",
        [
            (None, r"\IfFileExists{fontawesome.sty}"),
            ("", r"\IfFileExists{fontawesome.sty}"),
            ("/fonts/", r"\usepackage{fontspec}"),
            ("/usr/share/fonts/", r"Path=/usr/share/fonts/"),
        ],
    )
    def test_various_directories(
        self, font_dir: str | None, expected_fragment: str
    ) -> None:
        """Test with various font directory inputs."""
        result = fontawesome_support_block(font_dir)
        assert expected_fragment in result
