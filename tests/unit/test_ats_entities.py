"""Unit tests for ATS entity extractor."""

from __future__ import annotations

from simple_resume.core.ats import EntityExtractor, extract_entities

# Private functions being tested
from simple_resume.core.ats.entities import (
    _calculate_duration_years,
    _parse_date,
)


class TestEntityExtractor:
    """Test suite for EntityExtractor class."""

    def test_extract_basic_skills(self) -> None:
        """Test extraction of basic technical skills."""
        text = """
        Skills: Python, JavaScript, React, Docker, AWS
        """
        extractor = EntityExtractor()
        entities = extractor.extract(text)

        assert "Python" in entities.skills
        assert "JavaScript" in entities.skills
        assert "React" in entities.skills

    def test_extract_case_insensitive_skills(self) -> None:
        """Test that skill extraction is case-insensitive."""
        text = """
        Technologies: PYTHON, docker, aws
        """
        extractor = EntityExtractor()
        entities = extractor.extract(text)

        # Should find skills regardless of case
        assert len(entities.skills) > 0

    def test_extract_custom_skills(self) -> None:
        """Test extraction of custom skill patterns."""
        text = """
        My skills include Golang and Rust programming.
        """
        extractor = EntityExtractor(custom_skills=["Golang", "Rust"])
        entities = extractor.extract(text)

        assert "Golang" in entities.skills
        assert "Rust" in entities.skills

    def test_calculate_experience_from_date_ranges(self) -> None:
        """Test experience calculation from date ranges."""
        text = """
        Software Engineer
        Jan 2020 - Present
        """
        extractor = EntityExtractor()
        entities = extractor.extract(text)

        # Should calculate some years of experience
        assert entities.experience_years > 0

    def test_calculate_experience_multiple_positions(self) -> None:
        """Test experience calculation with multiple positions."""
        text = """
        Senior Developer
        Jan 2020 - Dec 2022

        Junior Developer
        Jan 2018 - Dec 2019
        """
        extractor = EntityExtractor()
        entities = extractor.extract(text)

        # Should accumulate experience from both positions
        assert entities.experience_years >= 4

    def test_calculate_experience_explicit_mention(self) -> None:
        """Test experience extraction from explicit mention."""
        text = """
        I have 5 years of experience in software development.
        """
        extractor = EntityExtractor()
        entities = extractor.extract(text)

        # Should detect explicit years mentioned
        assert entities.experience_years >= 5

    def test_extract_education_bachelor(self) -> None:
        """Test extraction of Bachelor's degree."""
        text = """
        Education
        Bachelor of Science in Computer Science from MIT
        """
        extractor = EntityExtractor()
        entities = extractor.extract(text)

        assert len(entities.degrees) > 0
        assert entities.degrees[0]["type"] == "Bachelor"

    def test_extract_education_master(self) -> None:
        """Test extraction of Master's degree."""
        text = """
        Academic
        Master of Science in Data Science, Stanford University
        """
        extractor = EntityExtractor()
        entities = extractor.extract(text)

        assert len(entities.degrees) > 0
        assert entities.degrees[0]["type"] == "Master"

    def test_extract_education_phd(self) -> None:
        """Test extraction of PhD degree."""
        text = """
        Education
        Ph.D. in Physics from Harvard
        """
        extractor = EntityExtractor()
        entities = extractor.extract(text)

        assert len(entities.degrees) > 0
        assert entities.degrees[0]["type"] == "PhD"

    def test_extract_certifications_aws(self) -> None:
        """Test extraction of AWS certification."""
        text = """
        Certifications
        AWS Certified Solutions Architect - Associate
        """
        extractor = EntityExtractor()
        entities = extractor.extract(text)

        assert len(entities.certifications) > 0

    def test_extract_certifications_multiple(self) -> None:
        """Test extraction of multiple certifications."""
        text = """
        Certifications
        - AWS Certified Solutions Architect
        - Google Cloud Certified
        - PMP
        """
        extractor = EntityExtractor()
        entities = extractor.extract(text)

        assert len(entities.certifications) >= 3

    def test_extract_keywords(self) -> None:
        """Test TF-IDF keyword extraction."""
        text = """
        Machine learning engineer with experience in Python, TensorFlow,
        neural networks, deep learning, and natural language processing.
        """
        extractor = EntityExtractor(extract_keywords=True)
        entities = extractor.extract(text)

        # Should extract keywords
        assert len(entities.keywords) > 0
        # Each keyword should be a tuple
        assert all(isinstance(k, tuple) and len(k) == 2 for k in entities.keywords)

    def test_extract_empty_text(self) -> None:
        """Test extraction from empty text."""
        extractor = EntityExtractor()
        entities = extractor.extract("")

        assert entities.skills == []
        assert entities.experience_years == 0.0
        assert entities.degrees == []
        assert entities.certifications == []

    def test_extract_minimal_text(self) -> None:
        """Test extraction from minimal text with no patterns."""
        text = "Some random text without patterns."
        extractor = EntityExtractor(extract_keywords=True)
        entities = extractor.extract(text)

        # Should return empty lists but not crash
        assert isinstance(entities.skills, list)
        assert isinstance(entities.degrees, list)
        assert isinstance(entities.certifications, list)

    def test_to_dict_serialization(self) -> None:
        """Test ExtractedEntities to_dict serialization."""
        text = """
        Skills: Python, Docker
        Experience: 5 years
        """
        extractor = EntityExtractor()
        entities = extractor.extract(text)

        result_dict = entities.to_dict()

        assert "skills" in result_dict
        assert "experience_years" in result_dict
        assert "degrees" in result_dict
        assert "certifications" in result_dict
        assert "keywords" in result_dict


class TestConvenienceFunction:
    """Test suite for extract_entities convenience function."""

    def test_convenience_function(self) -> None:
        """Test the extract_entities convenience function."""
        text = """
        Software Developer with 3 years experience.
        Skills: React, Python, SQL
        """
        entities = extract_entities(text)

        assert entities.experience_years >= 3
        assert len(entities.skills) > 0

    def test_convenience_function_with_kwargs(self) -> None:
        """Test extract_entities with custom arguments."""
        text = """
        My skills include Golang and Kubernetes.
        """
        entities = extract_entities(text, custom_skills=["Golang", "Kubernetes"])

        assert "Golang" in entities.skills
        assert "Kubernetes" in entities.skills


class TestDateParsing:
    """Test suite for date parsing utilities."""

    def test_parse_month_year_format(self) -> None:
        """Test parsing 'Month YYYY' format."""
        result = _parse_date("Jan 2020")
        assert result == (2020, 1)

        result = _parse_date("December 2019")
        assert result == (2019, 12)

    def test_parse_yyyy_mm_format(self) -> None:
        """Test parsing 'YYYY-MM' format."""
        result = _parse_date("2020-05")
        assert result == (2020, 5)

    def test_parse_yyyy_format(self) -> None:
        """Test parsing 'YYYY' format."""
        result = _parse_date("2020")
        assert result == (2020, 1)

    def test_parse_invalid_date(self) -> None:
        """Test parsing invalid date string."""
        result = _parse_date("invalid")
        assert result is None


class TestDurationCalculation:
    """Test suite for duration calculation utilities."""

    def test_duration_years_only(self) -> None:
        """Test duration calculation with full years."""
        result = _calculate_duration_years((2020, 1), (2023, 1))
        assert result == 3.0

    def test_duration_with_months(self) -> None:
        """Test duration calculation with partial years."""
        result = _calculate_duration_years((2020, 1), (2021, 7))
        assert result == 1.5

    def test_duration_to_present(self) -> None:
        """Test duration calculation when end date is None (present)."""
        result = _calculate_duration_years((2020, 1), None)
        # Should be approximately the number of years from 2020 to now
        assert result > 3
