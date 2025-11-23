"""Tests for Markdown to LaTeX conversion."""

from __future__ import annotations

from typing import Any

import pytest

from simple_resume.core.latex.conversion import (
    collect_blocks,
    convert_inline,
    normalize_iterable,
)


class TestConvertInline:
    """Tests for convert_inline function."""

    def test_plain_text(self) -> None:
        """Test conversion of plain text."""
        assert convert_inline("Hello World") == "Hello World"

    def test_bold_with_asterisks(self) -> None:
        """Test conversion of **bold** syntax."""
        result = convert_inline("This is **bold** text")
        assert r"\textbf{bold}" in result

    def test_bold_with_underscores(self) -> None:
        """Test conversion of __bold__ syntax."""
        result = convert_inline("This is __bold__ text")
        assert r"\textbf{bold}" in result

    def test_italic_with_single_asterisk(self) -> None:
        """Test conversion of *italic* syntax."""
        result = convert_inline("This is *italic* text")
        assert r"\textit{italic}" in result

    def test_italic_with_underscore(self) -> None:
        """Test conversion of _italic_ syntax."""
        result = convert_inline("This is _italic_ text")
        assert r"\textit{italic}" in result

    def test_code_with_backticks(self) -> None:
        """Test conversion of `code` syntax."""
        result = convert_inline("Use `print()` function")
        assert r"\texttt{print()}" in result

    def test_link_markdown(self) -> None:
        """Test conversion of [text](url) links."""
        result = convert_inline("[GitHub](https://github.com)")
        assert r"\href{https://github.com}{GitHub}" in result

    def test_link_with_special_chars_in_url(self) -> None:
        """Test link with special characters in URL."""
        result = convert_inline("[Search](https://example.com?q=test&foo=bar)")
        assert r"\href{https://example.com?q=test\&foo=bar}" in result

    def test_nested_bold_and_italic(self) -> None:
        """Test nested formatting."""
        result = convert_inline("Text with **bold and _italic_**")
        assert r"\textbf{" in result
        assert r"\textit{" in result

    def test_multiple_formats_in_text(self) -> None:
        """Test text with multiple formatting types."""
        result = convert_inline("**Bold**, *italic*, and `code`")
        assert r"\textbf{Bold}" in result
        assert r"\textit{italic}" in result
        assert r"\texttt{code}" in result

    def test_latex_escaping_in_plain_text(self) -> None:
        """Test that special LaTeX chars are escaped."""
        result = convert_inline("Price: $50 & up")
        assert r"\$50" in result
        assert r"\&" in result

    def test_latex_escaping_inside_code(self) -> None:
        """Test that code blocks escape LaTeX chars."""
        result = convert_inline("`$variable` and `function_name`")
        assert r"\texttt{\$variable}" in result
        assert r"\texttt{function\_name}" in result

    def test_url_escaping_in_links(self) -> None:
        """Test that URLs are properly escaped."""
        result = convert_inline("[Link](https://example.com/page#section)")
        assert r"\#section" in result

    def test_empty_string(self) -> None:
        """Test conversion of empty string."""
        assert convert_inline("") == ""

    def test_no_markdown(self) -> None:
        """Test text with no markdown formatting."""
        text = "Just plain text with no formatting."
        assert convert_inline(text) == text

    @pytest.mark.parametrize(
        "markdown,expected_latex_fragment",
        [
            ("**Python**", r"\textbf{Python}"),
            ("*emphasized*", r"\textit{emphasized}"),
            ("`code`", r"\texttt{code}"),
            ("[link](url)", r"\href{url}{link}"),
            ("C++", "C++"),
            ("file_name", r"file\_name"),
        ],
    )
    def test_various_conversions(
        self, markdown: str, expected_latex_fragment: str
    ) -> None:
        """Test various markdown to LaTeX conversions."""
        result = convert_inline(markdown)
        assert expected_latex_fragment in result


class TestCollectBlocks:
    """Tests for collect_blocks function."""

    def test_empty_description(self) -> None:
        """Test with None description."""
        assert collect_blocks(None) == []

    def test_empty_string(self) -> None:
        """Test with empty string."""
        assert collect_blocks("") == []

    def test_single_paragraph(self) -> None:
        """Test single paragraph."""
        blocks = collect_blocks("This is a simple paragraph.")
        assert len(blocks) == 1
        assert blocks[0]["kind"] == "paragraph"
        assert "simple paragraph" in blocks[0]["text"]

    def test_multiple_paragraphs(self) -> None:
        """Test multiple paragraphs separated by blank lines."""
        text = "First paragraph.\n\nSecond paragraph."
        blocks = collect_blocks(text)
        assert len(blocks) == 2
        assert blocks[0]["kind"] == "paragraph"
        assert blocks[1]["kind"] == "paragraph"

    def test_bullet_list(self) -> None:
        """Test unordered list with dashes."""
        text = "- First item\n- Second item\n- Third item"
        blocks = collect_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["kind"] == "itemize"
        assert len(blocks[0]["items"]) == 3

    def test_bullet_list_with_asterisks(self) -> None:
        """Test unordered list with asterisks."""
        text = "* First item\n* Second item"
        blocks = collect_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["kind"] == "itemize"

    def test_bullet_list_with_plus(self) -> None:
        """Test unordered list with plus signs."""
        text = "+ First item\n+ Second item"
        blocks = collect_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["kind"] == "itemize"

    def test_ordered_list(self) -> None:
        """Test ordered list."""
        text = "1. First item\n2. Second item\n3. Third item"
        blocks = collect_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["kind"] == "enumerate"
        assert len(blocks[0]["items"]) == 3

    def test_mixed_paragraph_and_list(self) -> None:
        """Test mixture of paragraphs and lists."""
        text = "Introduction paragraph.\n\n- Point one\n- Point two"
        blocks = collect_blocks(text)
        assert len(blocks) == 2
        assert blocks[0]["kind"] == "paragraph"
        assert blocks[1]["kind"] == "itemize"

    def test_list_item_continuation(self) -> None:
        """Test multi-line list items (indented continuation)."""
        text = "- First item\n  continued on next line\n- Second item"
        blocks = collect_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["kind"] == "itemize"
        assert "continued on next line" in blocks[0]["items"][0]

    def test_markdown_formatting_in_list_items(self) -> None:
        """Test that markdown is converted in list items."""
        text = "- Item with **bold** text\n- Item with `code`"
        blocks = collect_blocks(text)
        # First block should be a ListBlock
        assert len(blocks) > 0
        assert blocks[0]["kind"] == "itemize"
        assert r"\textbf{bold}" in blocks[0]["items"][0]
        assert r"\texttt{code}" in blocks[0]["items"][1]

    def test_markdown_formatting_in_paragraphs(self) -> None:
        """Test that markdown is converted in paragraphs."""
        text = "This has **bold** and *italic* text."
        blocks = collect_blocks(text)
        # First block should be a ParagraphBlock
        assert len(blocks) > 0
        assert blocks[0]["kind"] == "paragraph"
        assert r"\textbf{bold}" in blocks[0]["text"]
        assert r"\textit{italic}" in blocks[0]["text"]

    def test_blank_lines_between_list_items(self) -> None:
        """Test that blank lines separate lists."""
        text = "- First list\n\n- Second list"
        blocks = collect_blocks(text)
        assert len(blocks) == 2
        assert blocks[0]["kind"] == "itemize"
        assert blocks[1]["kind"] == "itemize"

    def test_switching_list_types(self) -> None:
        """Test switching between ordered and unordered lists."""
        text = "- Unordered item\n1. Ordered item"
        blocks = collect_blocks(text)
        assert len(blocks) == 2
        assert blocks[0]["kind"] == "itemize"
        assert blocks[1]["kind"] == "enumerate"

    def test_complex_document(self) -> None:
        """Test complex document with multiple block types."""
        text = """Introduction paragraph with **formatting**.

- First bullet
- Second bullet

Transition paragraph.

1. First numbered
2. Second numbered

Conclusion."""
        blocks = collect_blocks(text)
        assert len(blocks) == 5
        assert blocks[0]["kind"] == "paragraph"
        assert blocks[1]["kind"] == "itemize"
        assert blocks[2]["kind"] == "paragraph"
        assert blocks[3]["kind"] == "enumerate"
        assert blocks[4]["kind"] == "paragraph"


class TestNormalizeIterable:
    """Tests for normalize_iterable function."""

    def test_none_input(self) -> None:
        """Test with None input."""
        assert normalize_iterable(None) == []

    def test_string_input(self) -> None:
        """Test with single string."""
        result = normalize_iterable("single item")
        assert len(result) == 1
        assert "single item" in result[0]

    def test_list_input(self) -> None:
        """Test with list input."""
        result = normalize_iterable(["item1", "item2", "item3"])
        assert len(result) == 3

    def test_tuple_input(self) -> None:
        """Test with tuple input."""
        result = normalize_iterable(("item1", "item2"))
        assert len(result) == 2

    def test_set_input(self) -> None:
        """Test with set input."""
        result = normalize_iterable({"item1", "item2"})
        assert len(result) == 2

    def test_dict_input(self) -> None:
        """Test with dictionary input."""
        result = normalize_iterable({"Python": "Expert", "JavaScript": "Intermediate"})
        assert len(result) == 2
        # Dict items should be formatted as "key (value)"
        assert any("Python" in item and "Expert" in item for item in result)

    def test_dict_with_markdown(self) -> None:
        """Test that dict values are markdown-converted."""
        result = normalize_iterable({"Skill": "**Advanced**"})
        assert any(r"\textbf{Advanced}" in item for item in result)

    def test_list_with_markdown(self) -> None:
        """Test that list items are markdown-converted."""
        result = normalize_iterable(["*Python*", "`JavaScript`"])
        assert r"\textit{Python}" in result[0]
        assert r"\texttt{JavaScript}" in result[1]

    def test_mixed_types_in_list(self) -> None:
        """Test list with mixed types (converted to strings)."""
        result = normalize_iterable(["text", 123, True])
        assert len(result) == 3
        assert "123" in result[1]
        assert "True" in result[2]

    def test_empty_list(self) -> None:
        """Test with empty list."""
        assert normalize_iterable([]) == []

    def test_empty_dict(self) -> None:
        """Test with empty dict."""
        assert normalize_iterable({}) == []

    def test_latex_escaping_in_items(self) -> None:
        """Test that LaTeX special chars are escaped."""
        result = normalize_iterable(["C++", "C#", "$variable"])
        assert "C++" in result[0]
        assert r"C\#" in result[1]
        assert r"\$variable" in result[2]

    @pytest.mark.parametrize(
        "input_value,expected_length",
        [
            (None, 0),
            ("single", 1),
            (["a", "b"], 2),
            ({"x": "y", "z": "w"}, 2),
            ((1, 2, 3), 3),
        ],
    )
    def test_various_inputs(self, input_value: Any, expected_length: int) -> None:
        """Test various input types."""
        assert len(normalize_iterable(input_value)) == expected_length
