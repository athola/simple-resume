"""Unit tests for parse-once architecture (ParsedDocument and lazy evaluation).

Tests the efficiency pattern where text preprocessing is done once and cached
for reuse across multiple entity extraction operations.
"""

from __future__ import annotations

from simple_resume.core.ats.entities import (
    EntityExtractor,
    ParsedDocument,
    extract_entities,
    parse,
)


class TestParsedDocumentInitialization:
    """Test ParsedDocument creation and raw text storage."""

    def test_stores_raw_text(self):
        """Raw text is stored unchanged."""
        text = "  Hello   World  \n\n  Test  "
        doc = ParsedDocument(text)
        assert doc.raw_text == text

    def test_raw_text_is_immutable(self):
        """Raw text property returns same value every time."""
        doc = ParsedDocument("Test content")
        assert doc.raw_text == doc.raw_text

    def test_empty_text(self):
        """Handles empty string input."""
        doc = ParsedDocument("")
        assert doc.raw_text == ""
        assert doc.normalized_text == ""

    def test_whitespace_only_text(self):
        """Handles whitespace-only input."""
        doc = ParsedDocument("   \n\n\t   ")
        assert doc.normalized_text == ""


class TestParsedDocumentNormalizedText:
    """Test whitespace normalization in ParsedDocument."""

    def test_collapses_multiple_spaces(self):
        """Multiple spaces become single space."""
        doc = ParsedDocument("Hello    World")
        assert doc.normalized_text == "Hello World"

    def test_strips_leading_trailing_whitespace(self):
        """Strips whitespace from start and end."""
        doc = ParsedDocument("   Hello World   ")
        assert doc.normalized_text == "Hello World"

    def test_normalizes_line_endings(self):
        """Windows and Mac line endings become Unix newlines."""
        doc = ParsedDocument("Line1\r\nLine2\rLine3")
        assert "\r" not in doc.normalized_text
        assert "Line1" in doc.normalized_text
        assert "Line2" in doc.normalized_text
        assert "Line3" in doc.normalized_text

    def test_collapses_multiple_blank_lines(self):
        """Multiple blank lines become single blank line."""
        doc = ParsedDocument("Line1\n\n\n\nLine2")
        assert doc.normalized_text == "Line1\n\nLine2"

    def test_strips_each_line(self):
        """Leading/trailing whitespace removed from each line."""
        doc = ParsedDocument("   Line1   \n   Line2   ")
        assert doc.normalized_text == "Line1\nLine2"

    def test_preserves_single_newlines(self):
        """Single newlines between content are preserved."""
        doc = ParsedDocument("Line1\nLine2\nLine3")
        assert doc.normalized_text == "Line1\nLine2\nLine3"


class TestParsedDocumentLowercaseText:
    """Test lowercase text property."""

    def test_converts_to_lowercase(self):
        """Text is converted to lowercase."""
        doc = ParsedDocument("Hello WORLD Test")
        assert doc.lowercase_text == "hello world test"

    def test_uses_normalized_text(self):
        """Lowercase is derived from normalized text."""
        doc = ParsedDocument("  HELLO   WORLD  ")
        assert doc.lowercase_text == "hello world"


class TestParsedDocumentLines:
    """Test line extraction."""

    def test_extracts_non_empty_lines(self):
        """Returns list of non-empty lines."""
        doc = ParsedDocument("Line1\n\nLine2\nLine3")
        assert doc.lines == ["Line1", "Line2", "Line3"]

    def test_excludes_empty_lines(self):
        """Empty lines are filtered out."""
        doc = ParsedDocument("A\n\n\nB")
        assert "" not in doc.lines

    def test_empty_text_returns_empty_list(self):
        """Empty input returns empty list."""
        doc = ParsedDocument("")
        assert doc.lines == []


class TestParsedDocumentSentences:
    """Test sentence splitting."""

    def test_splits_on_period(self):
        """Splits sentences on period followed by space."""
        doc = ParsedDocument("First sentence. Second sentence. Third.")
        assert len(doc.sentences) >= 2
        assert "First sentence." in doc.sentences[0]

    def test_splits_on_question_mark(self):
        """Splits on question marks."""
        doc = ParsedDocument("What is this? This is a test.")
        assert len(doc.sentences) == 2

    def test_splits_on_exclamation(self):
        """Splits on exclamation marks."""
        doc = ParsedDocument("Hello! Welcome to our company.")
        assert len(doc.sentences) == 2

    def test_filters_empty_sentences(self):
        """Empty strings are filtered from results."""
        doc = ParsedDocument("One.  Two.")
        assert all(s.strip() for s in doc.sentences)


class TestParsedDocumentWordTokens:
    """Test word token extraction."""

    def test_extracts_alphabetic_words(self):
        """Extracts words containing only letters."""
        doc = ParsedDocument("Hello World 123 Test")
        assert "Hello" in doc.word_tokens
        assert "World" in doc.word_tokens
        assert "Test" in doc.word_tokens
        assert "123" not in doc.word_tokens

    def test_excludes_numbers(self):
        """Numbers are not included in word tokens."""
        doc = ParsedDocument("Year 2024 was great")
        assert "2024" not in doc.word_tokens

    def test_splits_on_punctuation(self):
        """Words are split on punctuation."""
        doc = ParsedDocument("Hello,World;Test")
        assert "Hello" in doc.word_tokens
        assert "World" in doc.word_tokens


class TestParsedDocumentFindSection:
    """Test section finding functionality."""

    def test_finds_section_by_header(self):
        """Finds section content by header pattern."""
        doc = ParsedDocument("Skills: Python, JavaScript\n\nExperience: 5 years")
        skills = doc.find_section(r"Skills")
        assert skills is not None
        assert "Python" in skills

    def test_returns_none_for_missing_section(self):
        """Returns None when section not found."""
        doc = ParsedDocument("Experience: 5 years\n\nEducation: BS")
        result = doc.find_section(r"Certifications")
        assert result is None

    def test_case_insensitive_header(self):
        """Section headers are matched case-insensitively."""
        doc = ParsedDocument("SKILLS: Python, Java\n\nOther content")
        skills = doc.find_section(r"skills")
        assert skills is not None

    def test_multiple_header_patterns(self):
        """Supports regex patterns with alternatives."""
        doc = ParsedDocument("Tech Stack: React, Vue\n\nExperience: 3 years")
        skills = doc.find_section(r"Skills|Tech Stack")
        assert skills is not None
        assert "React" in skills


class TestParsedDocumentLazyEvaluation:
    """Test that properties are lazily evaluated and cached."""

    def test_normalized_text_computed_once(self):
        """Normalized text is computed once and cached."""
        doc = ParsedDocument("  Test  ")
        # Access multiple times
        result1 = doc.normalized_text
        result2 = doc.normalized_text
        # Should be same object (cached)
        assert result1 is result2

    def test_lines_computed_once(self):
        """Lines list is computed once and cached."""
        doc = ParsedDocument("Line1\nLine2")
        result1 = doc.lines
        result2 = doc.lines
        assert result1 is result2

    def test_sentences_computed_once(self):
        """Sentences list is computed once and cached."""
        doc = ParsedDocument("First. Second.")
        result1 = doc.sentences
        result2 = doc.sentences
        assert result1 is result2

    def test_word_tokens_computed_once(self):
        """Word tokens list is computed once and cached."""
        doc = ParsedDocument("Hello World")
        result1 = doc.word_tokens
        result2 = doc.word_tokens
        assert result1 is result2

    def test_lowercase_computed_once(self):
        """Lowercase text is computed once and cached."""
        doc = ParsedDocument("Hello World")
        result1 = doc.lowercase_text
        result2 = doc.lowercase_text
        assert result1 is result2


class TestParseFunction:
    """Test the parse() entry point function."""

    def test_returns_parsed_document(self):
        """parse() returns a ParsedDocument instance."""
        doc = parse("Test content")
        assert isinstance(doc, ParsedDocument)

    def test_stores_text(self):
        """Returned document stores the input text."""
        text = "Resume content here"
        doc = parse(text)
        assert doc.raw_text == text

    def test_empty_string(self):
        """Handles empty string input."""
        doc = parse("")
        assert doc.raw_text == ""


class TestEntityExtractorWithParsedDocument:
    """Test EntityExtractor accepting ParsedDocument inputs."""

    def test_extract_accepts_string(self):
        """extract() accepts string input."""
        extractor = EntityExtractor()
        result = extractor.extract("Python developer with 5 years experience")
        assert result is not None

    def test_extract_accepts_parsed_document(self):
        """extract() accepts ParsedDocument input."""
        doc = ParsedDocument("Python developer with 5 years experience")
        extractor = EntityExtractor()
        result = extractor.extract(doc)
        assert result is not None

    def test_same_results_for_string_and_document(self):
        """String and ParsedDocument inputs produce same results."""
        text = "Python, JavaScript, React developer. Skills: AWS, Docker"

        extractor = EntityExtractor()
        string_result = extractor.extract(text)
        doc_result = extractor.extract(ParsedDocument(text))

        # Should extract same skills
        assert set(string_result.skills) == set(doc_result.skills)

    def test_ensure_parsed_returns_document_unchanged(self):
        """_ensure_parsed returns ParsedDocument unchanged."""
        doc = ParsedDocument("Test")
        extractor = EntityExtractor()
        result = extractor._ensure_parsed(doc)
        assert result is doc  # Same object

    def test_ensure_parsed_wraps_string(self):
        """_ensure_parsed wraps string in ParsedDocument."""
        extractor = EntityExtractor()
        result = extractor._ensure_parsed("Test string")
        assert isinstance(result, ParsedDocument)
        assert result.raw_text == "Test string"


class TestExtractEntitiesFunction:
    """Test the extract_entities() convenience function."""

    def test_accepts_string(self):
        """extract_entities() accepts string input."""
        result = extract_entities("Python developer")
        assert result is not None

    def test_accepts_parsed_document(self):
        """extract_entities() accepts ParsedDocument input."""
        doc = parse("Python developer")
        result = extract_entities(doc)
        assert result is not None

    def test_passes_kwargs_to_extractor(self):
        """Kwargs are passed to EntityExtractor."""
        # With keywords disabled
        result = extract_entities("Test content", extract_keywords=False)
        assert result.keywords == []


class TestParseOnceEfficiency:
    """Test that parse-once pattern provides efficiency benefits."""

    def test_reuses_preprocessing_across_extractions(self):
        """Same ParsedDocument can be reused for multiple extractions."""
        text = """
        Skills: Python, JavaScript, Docker

        Experience:
        Senior Developer at TechCorp
        Jan 2020 - Present

        Education:
        Bachelor's in Computer Science
        """

        # Parse once
        doc = parse(text)

        # Extract multiple times (simulating different extractors)
        extractor1 = EntityExtractor(extract_keywords=True)
        extractor2 = EntityExtractor(extract_keywords=False)

        result1 = extractor1.extract(doc)
        result2 = extractor2.extract(doc)

        # Both should work
        assert result1.skills is not None
        assert result2.skills is not None
        # Same skills extracted (proof they used same preprocessed data)
        assert set(result1.skills) == set(result2.skills)

    def test_document_properties_not_computed_until_accessed(self):
        """Cached properties are not computed until first access."""
        doc = ParsedDocument("Test content")

        # Check that cache is empty before access
        # (cached_property stores in __dict__ when first accessed)
        assert "normalized_text" not in doc.__dict__

        # Access the property
        _ = doc.normalized_text

        # Now it should be cached
        assert "normalized_text" in doc.__dict__


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_text(self):
        """Handles very long text input."""
        long_text = "Word " * 10000
        doc = ParsedDocument(long_text)
        assert len(doc.normalized_text) > 0
        assert len(doc.word_tokens) == 10000

    def test_unicode_content(self):
        """Handles unicode characters."""
        doc = ParsedDocument("Python 开发者 with résumé")
        assert "Python" in doc.normalized_text
        assert "开发者" in doc.normalized_text

    def test_special_characters(self):
        """Handles special characters in text."""
        doc = ParsedDocument("C++ & C# developer @ tech company")
        assert "C++" in doc.normalized_text
        assert "C#" in doc.normalized_text

    def test_mixed_encoding_line_endings(self):
        """Handles documents with mixed line ending styles."""
        doc = ParsedDocument("Line1\r\nLine2\nLine3\rLine4")
        lines = doc.lines
        assert len(lines) == 4
