"""Tests for Markdown to LaTeX conversion."""

from __future__ import annotations

from typing import Any

import pytest

from simple_resume.core.latex.conversion import (
    collect_blocks,
    convert_inline,
    normalize_iterable,
)
from tests.bdd import Scenario


class TestConvertInline:
    """Tests for convert_inline function."""

    def test_plain_text(self, story: Scenario) -> None:
        """Test conversion of plain text."""
        story.given("plain text without markdown")
        story.when("converting inline")
        assert convert_inline("Hello World") == "Hello World"

    def test_bold_with_asterisks(self, story: Scenario) -> None:
        """Test conversion of **bold** syntax."""
        story.given("text with **bold** asterisks syntax")
        story.when("converting inline")
        result = convert_inline("This is **bold** text")
        assert r"\textbf{bold}" in result

    def test_bold_with_underscores(self, story: Scenario) -> None:
        """Test conversion of __bold__ syntax."""
        story.given("text with __bold__ underscore syntax")
        story.when("converting inline")
        result = convert_inline("This is __bold__ text")
        assert r"\textbf{bold}" in result

    def test_italic_with_single_asterisk(self, story: Scenario) -> None:
        """Test conversion of *italic* syntax."""
        story.given("text with *italic* single asterisk syntax")
        story.when("converting inline")
        result = convert_inline("This is *italic* text")
        assert r"\textit{italic}" in result

    def test_italic_with_underscore(self, story: Scenario) -> None:
        """Test conversion of _italic_ syntax."""
        story.given("text with _italic_ underscore syntax")
        story.when("converting inline")
        result = convert_inline("This is _italic_ text")
        assert r"\textit{italic}" in result

    def test_code_with_backticks(self, story: Scenario) -> None:
        """Test conversion of `code` syntax."""
        story.given("text with `code` backtick syntax")
        story.when("converting inline")
        result = convert_inline("Use `print()` function")
        assert r"\texttt{print()}" in result

    def test_link_markdown(self, story: Scenario) -> None:
        """Test conversion of [text](url) links."""
        story.given("markdown link [text](url)")
        story.when("converting inline")
        result = convert_inline("[GitHub](https://github.com)")
        assert r"\href{https://github.com}{GitHub}" in result

    def test_link_with_special_chars_in_url(self, story: Scenario) -> None:
        """Test link with special characters in URL."""
        story.given("a markdown link with special characters in URL")
        story.when("converting inline")
        result = convert_inline("[Search](https://example.com?q=test&foo=bar)")
        assert r"\href{https://example.com?q=test\&foo=bar}" in result

    def test_nested_bold_and_italic(self, story: Scenario) -> None:
        """Test nested formatting."""
        story.given("text with nested bold and italic formatting")
        story.when("converting inline")
        result = convert_inline("Text with **bold and _italic_**")
        assert r"\textbf{" in result
        assert r"\textit{" in result

    def test_multiple_formats_in_text(self, story: Scenario) -> None:
        """Test text with multiple formatting types."""
        story.given("text with bold, italic, and code formatting")
        story.when("converting inline")
        result = convert_inline("**Bold**, *italic*, and `code`")
        assert r"\textbf{Bold}" in result
        assert r"\textit{italic}" in result
        assert r"\texttt{code}" in result

    def test_latex_escaping_in_plain_text(self, story: Scenario) -> None:
        """Test that special LaTeX chars are escaped."""
        story.given("text containing LaTeX special characters")
        story.when("converting inline")
        result = convert_inline("Price: $50 & up")
        assert r"\$50" in result
        assert r"\&" in result

    def test_latex_escaping_inside_code(self, story: Scenario) -> None:
        """Test that code blocks escape LaTeX chars."""
        story.given("code blocks containing LaTeX special characters")
        story.when("converting inline")
        result = convert_inline("`$variable` and `function_name`")
        assert r"\texttt{\$variable}" in result
        assert r"\texttt{function\_name}" in result

    def test_url_escaping_in_links(self, story: Scenario) -> None:
        """Test that URLs are properly escaped."""
        story.given("a link URL with hash fragment")
        story.when("converting inline")
        result = convert_inline("[Link](https://example.com/page#section)")
        assert r"\#section" in result

    def test_empty_string(self, story: Scenario) -> None:
        """Test conversion of empty string."""
        story.given("an empty string")
        story.when("converting inline")
        assert convert_inline("") == ""

    def test_no_markdown(self, story: Scenario) -> None:
        """Test text with no markdown formatting."""
        story.given("plain text with no markdown formatting")
        story.when("converting inline")
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
        self, markdown: str, expected_latex_fragment: str, story: Scenario
    ) -> None:
        """Test various markdown to LaTeX conversions."""
        story.given(f"markdown text '{markdown}'")
        story.when("converting inline")
        result = convert_inline(markdown)
        assert expected_latex_fragment in result


class TestCollectBlocks:
    """Tests for collect_blocks function."""

    def test_empty_description(self, story: Scenario) -> None:
        """Test with None description."""
        story.given("None as description input")
        story.when("collecting blocks")
        assert collect_blocks(None) == []

    def test_empty_string(self, story: Scenario) -> None:
        """Test with empty string."""
        story.given("an empty string as description")
        story.when("collecting blocks")
        assert collect_blocks("") == []

    def test_single_paragraph(self, story: Scenario) -> None:
        """Test single paragraph."""
        story.given("a single paragraph of text")
        story.when("collecting blocks")
        blocks = collect_blocks("This is a simple paragraph.")
        assert len(blocks) == 1
        assert blocks[0]["kind"] == "paragraph"
        assert "simple paragraph" in blocks[0]["text"]

    def test_multiple_paragraphs(self, story: Scenario) -> None:
        """Test multiple paragraphs separated by blank lines."""
        story.given("multiple paragraphs separated by blank lines")
        story.when("collecting blocks")
        text = "First paragraph.\n\nSecond paragraph."
        blocks = collect_blocks(text)
        assert len(blocks) == 2
        assert blocks[0]["kind"] == "paragraph"
        assert blocks[1]["kind"] == "paragraph"

    def test_bullet_list(self, story: Scenario) -> None:
        """Test unordered list with dashes."""
        story.given("an unordered list using dashes")
        story.when("collecting blocks")
        text = "- First item\n- Second item\n- Third item"
        blocks = collect_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["kind"] == "itemize"
        assert len(blocks[0]["items"]) == 3

    def test_bullet_list_with_asterisks(self, story: Scenario) -> None:
        """Test unordered list with asterisks."""
        story.given("an unordered list using asterisks")
        story.when("collecting blocks")
        text = "* First item\n* Second item"
        blocks = collect_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["kind"] == "itemize"

    def test_bullet_list_with_plus(self, story: Scenario) -> None:
        """Test unordered list with plus signs."""
        story.given("an unordered list using plus signs")
        story.when("collecting blocks")
        text = "+ First item\n+ Second item"
        blocks = collect_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["kind"] == "itemize"

    def test_ordered_list(self, story: Scenario) -> None:
        """Test ordered list."""
        story.given("an ordered/numbered list")
        story.when("collecting blocks")
        text = "1. First item\n2. Second item\n3. Third item"
        blocks = collect_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["kind"] == "enumerate"
        assert len(blocks[0]["items"]) == 3

    def test_mixed_paragraph_and_list(self, story: Scenario) -> None:
        """Test mixture of paragraphs and lists."""
        story.given("a paragraph followed by a list")
        story.when("collecting blocks")
        text = "Introduction paragraph.\n\n- Point one\n- Point two"
        blocks = collect_blocks(text)
        assert len(blocks) == 2
        assert blocks[0]["kind"] == "paragraph"
        assert blocks[1]["kind"] == "itemize"

    def test_list_item_continuation(self, story: Scenario) -> None:
        """Test multi-line list items (indented continuation)."""
        story.given("a list item with indented continuation line")
        story.when("collecting blocks")
        text = "- First item\n  continued on next line\n- Second item"
        blocks = collect_blocks(text)
        assert len(blocks) == 1
        assert blocks[0]["kind"] == "itemize"
        assert "continued on next line" in blocks[0]["items"][0]

    def test_markdown_formatting_in_list_items(self, story: Scenario) -> None:
        """Test that markdown is converted in list items."""
        story.given("list items containing markdown formatting")
        story.when("collecting blocks")
        text = "- Item with **bold** text\n- Item with `code`"
        blocks = collect_blocks(text)
        # First block should be a ListBlock
        assert len(blocks) > 0
        assert blocks[0]["kind"] == "itemize"
        assert r"\textbf{bold}" in blocks[0]["items"][0]
        assert r"\texttt{code}" in blocks[0]["items"][1]

    def test_markdown_formatting_in_paragraphs(self, story: Scenario) -> None:
        """Test that markdown is converted in paragraphs."""
        story.given("a paragraph with markdown formatting")
        story.when("collecting blocks")
        text = "This has **bold** and *italic* text."
        blocks = collect_blocks(text)
        # First block should be a ParagraphBlock
        assert len(blocks) > 0
        assert blocks[0]["kind"] == "paragraph"
        assert r"\textbf{bold}" in blocks[0]["text"]
        assert r"\textit{italic}" in blocks[0]["text"]

    def test_blank_lines_between_list_items(self, story: Scenario) -> None:
        """Test that blank lines separate lists."""
        story.given("list items separated by blank lines")
        story.when("collecting blocks")
        text = "- First list\n\n- Second list"
        blocks = collect_blocks(text)
        assert len(blocks) == 2
        assert blocks[0]["kind"] == "itemize"
        assert blocks[1]["kind"] == "itemize"

    def test_switching_list_types(self, story: Scenario) -> None:
        """Test switching between ordered and unordered lists."""
        story.given("text switching from unordered to ordered list")
        story.when("collecting blocks")
        text = "- Unordered item\n1. Ordered item"
        blocks = collect_blocks(text)
        assert len(blocks) == 2
        assert blocks[0]["kind"] == "itemize"
        assert blocks[1]["kind"] == "enumerate"

    def test_complex_document(self, story: Scenario) -> None:
        """Test complex document with multiple block types."""
        story.given("a complex document with paragraphs, bullets, and numbered lists")
        story.when("collecting blocks")
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

    def test_none_input(self, story: Scenario) -> None:
        """Test with None input."""
        story.given("None as input")
        story.when("normalizing iterable")
        assert normalize_iterable(None) == []

    def test_string_input(self, story: Scenario) -> None:
        """Test with single string."""
        story.given("a single string")
        story.when("normalizing iterable")
        result = normalize_iterable("single item")
        assert len(result) == 1
        assert "single item" in result[0]

    def test_list_input(self, story: Scenario) -> None:
        """Test with list input."""
        story.given("a list of strings")
        story.when("normalizing iterable")
        result = normalize_iterable(["item1", "item2", "item3"])
        assert len(result) == 3

    def test_tuple_input(self, story: Scenario) -> None:
        """Test with tuple input."""
        story.given("a tuple of strings")
        story.when("normalizing iterable")
        result = normalize_iterable(("item1", "item2"))
        assert len(result) == 2

    def test_set_input(self, story: Scenario) -> None:
        """Test with set input."""
        story.given("a set of strings")
        story.when("normalizing iterable")
        result = normalize_iterable({"item1", "item2"})
        assert len(result) == 2

    def test_dict_input(self, story: Scenario) -> None:
        """Test with dictionary input."""
        story.given("a dictionary of skills to proficiency levels")
        story.when("normalizing iterable")
        result = normalize_iterable({"Python": "Expert", "JavaScript": "Intermediate"})
        assert len(result) == 2
        # Dict items should be formatted as "key (value)"
        assert any("Python" in item and "Expert" in item for item in result)

    def test_dict_with_markdown(self, story: Scenario) -> None:
        """Test that dict values are markdown-converted."""
        story.given("a dictionary with markdown-formatted values")
        story.when("normalizing iterable")
        result = normalize_iterable({"Skill": "**Advanced**"})
        assert any(r"\textbf{Advanced}" in item for item in result)

    def test_list_with_markdown(self, story: Scenario) -> None:
        """Test that list items are markdown-converted."""
        story.given("a list with markdown-formatted items")
        story.when("normalizing iterable")
        result = normalize_iterable(["*Python*", "`JavaScript`"])
        assert r"\textit{Python}" in result[0]
        assert r"\texttt{JavaScript}" in result[1]

    def test_mixed_types_in_list(self, story: Scenario) -> None:
        """Test list with mixed types (converted to strings)."""
        story.given("a list with mixed types (string, int, bool)")
        story.when("normalizing iterable")
        result = normalize_iterable(["text", 123, True])
        assert len(result) == 3
        assert "123" in result[1]
        assert "True" in result[2]

    def test_empty_list(self, story: Scenario) -> None:
        """Test with empty list."""
        story.given("an empty list")
        story.when("normalizing iterable")
        assert normalize_iterable([]) == []

    def test_empty_dict(self, story: Scenario) -> None:
        """Test with empty dict."""
        story.given("an empty dictionary")
        story.when("normalizing iterable")
        assert normalize_iterable({}) == []

    def test_latex_escaping_in_items(self, story: Scenario) -> None:
        """Test that LaTeX special chars are escaped."""
        story.given("list items containing LaTeX special characters")
        story.when("normalizing iterable")
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
    def test_various_inputs(
        self, input_value: Any, expected_length: int, story: Scenario
    ) -> None:
        """Test various input types."""
        story.given(f"input of type {type(input_value).__name__}")
        story.when("normalizing iterable")
        assert len(normalize_iterable(input_value)) == expected_length
