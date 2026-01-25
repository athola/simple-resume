"""Unit tests for ATS base classes and validation.

Tests the base scorer, dataclasses, enums, and validation logic
in the ATS scoring system.
"""

from __future__ import annotations

from typing import Any

import pytest

from simple_resume.core.ats.base import (
    BaseScorer,
    Degree,
    DegreeType,
    ExtractedEntities,
    ScorerResult,
)


# Concrete implementation of BaseScorer for testing
class ConcreteScorer(BaseScorer):
    """Concrete scorer implementation for testing BaseScorer."""

    def score(
        self,
        resume_text: str,
        job_description: str,
        **kwargs: Any,
    ) -> ScorerResult:
        """Return a simple test result."""
        return ScorerResult(
            name="test_scorer",
            score=0.5,
            weight=self.weight,
        )


class TestBaseScorerValidation:
    """Tests for BaseScorer weight validation."""

    def test_valid_weight_zero(self):
        """Test that weight=0.0 is valid."""
        scorer = ConcreteScorer(weight=0.0)
        assert scorer.weight == 0.0

    def test_valid_weight_one(self):
        """Test that weight=1.0 is valid."""
        scorer = ConcreteScorer(weight=1.0)
        assert scorer.weight == 1.0

    def test_valid_weight_midpoint(self):
        """Test that weight=0.5 is valid."""
        scorer = ConcreteScorer(weight=0.5)
        assert scorer.weight == 0.5

    def test_invalid_weight_negative(self):
        """Test that negative weight raises ValueError."""
        with pytest.raises(ValueError, match="weight must be in"):
            ConcreteScorer(weight=-0.1)

    def test_invalid_weight_above_one(self):
        """Test that weight > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="weight must be in"):
            ConcreteScorer(weight=1.1)

    def test_invalid_weight_large_negative(self):
        """Test that large negative weight raises ValueError."""
        with pytest.raises(ValueError, match="weight must be in"):
            ConcreteScorer(weight=-100.0)

    def test_invalid_weight_large_positive(self):
        """Test that large positive weight raises ValueError."""
        with pytest.raises(ValueError, match="weight must be in"):
            ConcreteScorer(weight=100.0)

    def test_default_weight_is_one(self):
        """Test that default weight is 1.0."""
        scorer = ConcreteScorer()
        assert scorer.weight == 1.0


class TestScorerResult:
    """Tests for ScorerResult dataclass."""

    def test_valid_result(self):
        """Test creating a valid ScorerResult."""
        result = ScorerResult(
            name="test",
            score=0.75,
            weight=0.5,
            details={"key": "value"},
            component_scores={"comp1": 0.8, "comp2": 0.6},
        )
        assert result.name == "test"
        assert result.score == 0.75
        assert result.weight == 0.5
        assert result.details == {"key": "value"}
        assert result.component_scores == {"comp1": 0.8, "comp2": 0.6}

    def test_weighted_score_property(self):
        """Test weighted_score calculation."""
        result = ScorerResult(name="test", score=0.8, weight=0.5)
        assert result.weighted_score == 0.4

    def test_invalid_score_negative(self):
        """Test that negative score raises ValueError."""
        with pytest.raises(ValueError, match="score must be in"):
            ScorerResult(name="test", score=-0.1)

    def test_invalid_score_above_one(self):
        """Test that score > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="score must be in"):
            ScorerResult(name="test", score=1.1)

    def test_invalid_weight_negative(self):
        """Test that negative weight raises ValueError."""
        with pytest.raises(ValueError, match="weight must be in"):
            ScorerResult(name="test", score=0.5, weight=-0.1)

    def test_invalid_weight_above_one(self):
        """Test that weight > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="weight must be in"):
            ScorerResult(name="test", score=0.5, weight=1.1)

    def test_invalid_component_score(self):
        """Test that invalid component score raises ValueError."""
        with pytest.raises(ValueError, match="component_scores"):
            ScorerResult(
                name="test",
                score=0.5,
                component_scores={"bad_comp": 1.5},
            )

    def test_to_dict(self):
        """Test to_dict serialization."""
        result = ScorerResult(
            name="test",
            score=0.8,
            weight=0.5,
            details={"key": "value"},
            component_scores={"comp1": 0.9},
        )
        d = result.to_dict()
        assert d["name"] == "test"
        assert d["score"] == 0.8
        assert d["weight"] == 0.5
        assert d["weighted_score"] == 0.4
        assert d["details"] == {"key": "value"}
        assert d["component_scores"] == {"comp1": 0.9}


class TestDegreeType:
    """Tests for DegreeType enum."""

    def test_all_degree_types_exist(self):
        """Test that all expected degree types exist."""
        expected = [
            "ASSOCIATE",
            "BACHELOR",
            "MASTER",
            "PHD",
            "CERTIFICATE",
            "DIPLOMA",
            "OTHER",
        ]
        for name in expected:
            assert hasattr(DegreeType, name)

    def test_from_string_exact_match(self):
        """Test from_string with exact matches."""
        assert DegreeType.from_string("Bachelor") == DegreeType.BACHELOR
        assert DegreeType.from_string("Master") == DegreeType.MASTER
        assert DegreeType.from_string("PhD") == DegreeType.PHD

    def test_from_string_case_insensitive(self):
        """Test from_string is case insensitive."""
        assert DegreeType.from_string("BACHELOR") == DegreeType.BACHELOR
        assert DegreeType.from_string("bachelor") == DegreeType.BACHELOR
        assert DegreeType.from_string("BaChElOr") == DegreeType.BACHELOR

    def test_from_string_aliases(self):
        """Test from_string handles common aliases."""
        assert DegreeType.from_string("Doctorate") == DegreeType.PHD
        assert DegreeType.from_string("BS") == DegreeType.BACHELOR
        assert DegreeType.from_string("BA") == DegreeType.BACHELOR
        assert DegreeType.from_string("MS") == DegreeType.MASTER
        assert DegreeType.from_string("MA") == DegreeType.MASTER
        assert DegreeType.from_string("MBA") == DegreeType.MASTER
        assert DegreeType.from_string("AA") == DegreeType.ASSOCIATE
        assert DegreeType.from_string("Cert") == DegreeType.CERTIFICATE

    def test_from_string_unknown_returns_other(self):
        """Test from_string returns OTHER for unknown values."""
        assert DegreeType.from_string("Unknown Degree") == DegreeType.OTHER
        assert DegreeType.from_string("Foo Bar") == DegreeType.OTHER

    def test_from_string_strips_whitespace(self):
        """Test from_string strips whitespace."""
        assert DegreeType.from_string("  Bachelor  ") == DegreeType.BACHELOR

    def test_from_string_empty_returns_other(self):
        """Test from_string returns OTHER for empty string."""
        assert DegreeType.from_string("") == DegreeType.OTHER
        assert DegreeType.from_string("   ") == DegreeType.OTHER

    def test_str_enum_comparison(self):
        """Test DegreeType can be compared as string."""
        assert DegreeType.BACHELOR == "Bachelor"
        assert DegreeType.PHD == "PhD"

    def test_is_recognized_known_types(self):
        """Test is_recognized returns True for known degree types."""
        assert DegreeType.is_recognized("Bachelor") is True
        assert DegreeType.is_recognized("master") is True
        assert DegreeType.is_recognized("PhD") is True
        assert DegreeType.is_recognized("BS") is True
        assert DegreeType.is_recognized("MBA") is True

    def test_is_recognized_unknown_types(self):
        """Test is_recognized returns False for unknown degree types."""
        assert DegreeType.is_recognized("Unknown Degree") is False
        assert DegreeType.is_recognized("Foo") is False
        assert DegreeType.is_recognized("") is False


class TestDegree:
    """Tests for Degree dataclass."""

    def test_create_with_enum(self):
        """Test creating Degree with DegreeType enum."""
        degree = Degree(type=DegreeType.BACHELOR, school="MIT", field="CS")
        assert degree.type == DegreeType.BACHELOR
        assert degree.school == "MIT"
        assert degree.field == "CS"

    def test_create_with_string(self):
        """Test creating Degree with string type (auto-converts)."""
        degree = Degree(type="Bachelor", school="MIT", field="CS")
        assert degree.type == DegreeType.BACHELOR
        assert degree.type_value == "Bachelor"

    def test_create_with_alias_string(self):
        """Test creating Degree with alias string."""
        degree = Degree(type="BS", school="MIT")
        assert degree.type == DegreeType.BACHELOR

    def test_default_school(self):
        """Test default school is 'Unknown'."""
        degree = Degree(type=DegreeType.BACHELOR)
        assert degree.school == "Unknown"

    def test_default_field_empty(self):
        """Test default field is empty string."""
        degree = Degree(type=DegreeType.BACHELOR)
        assert degree.field == ""

    def test_type_value_property(self):
        """Test type_value returns string value."""
        degree = Degree(type=DegreeType.PHD, school="Stanford")
        assert degree.type_value == "PhD"

    def test_to_dict(self):
        """Test to_dict serialization."""
        degree = Degree(type=DegreeType.MASTER, school="Harvard", field="MBA")
        d = degree.to_dict()
        assert d["type"] == "Master"
        assert d["school"] == "Harvard"
        assert d["field"] == "MBA"

    def test_empty_string_type_raises_error(self):
        """Test that empty string type raises ValueError."""
        with pytest.raises(ValueError, match="Degree type cannot be empty"):
            Degree(type="", school="MIT")

    def test_whitespace_only_type_raises_error(self):
        """Test that whitespace-only string type raises ValueError."""
        with pytest.raises(ValueError, match="Degree type cannot be empty"):
            Degree(type="   ", school="MIT")


class TestExtractedEntities:
    """Tests for ExtractedEntities dataclass."""

    def test_defaults(self):
        """Test default values."""
        entities = ExtractedEntities()
        assert entities.skills == []
        assert entities.experience_years == 0.0
        assert entities.degrees == []
        assert entities.certifications == []
        assert entities.keywords == []

    def test_with_values(self):
        """Test creating with values."""
        degree = Degree(type=DegreeType.BACHELOR, school="MIT")
        entities = ExtractedEntities(
            skills=["Python", "AWS"],
            experience_years=5.5,
            degrees=[degree],
            certifications=["AWS SAA"],
            keywords=[("python", 0.8), ("aws", 0.6)],
        )
        assert entities.skills == ["Python", "AWS"]
        assert entities.experience_years == 5.5
        assert len(entities.degrees) == 1
        assert entities.certifications == ["AWS SAA"]
        assert len(entities.keywords) == 2

    def test_to_dict(self):
        """Test to_dict serialization."""
        degree = Degree(type=DegreeType.BACHELOR, school="MIT", field="CS")
        entities = ExtractedEntities(
            skills=["Python"],
            experience_years=3.0,
            degrees=[degree],
            certifications=["PMP"],
            keywords=[("python", 0.9)],
        )
        d = entities.to_dict()
        assert d["skills"] == ["Python"]
        assert d["experience_years"] == 3.0
        assert len(d["degrees"]) == 1
        assert d["degrees"][0]["type"] == "Bachelor"
        assert d["certifications"] == ["PMP"]
        assert d["keywords"] == [("python", 0.9)]
