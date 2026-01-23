"""Base classes and interfaces for ATS scoring algorithms.

All scorers must inherit from BaseScorer and implement the score() method.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from simple_resume.core.ats.constants import validate_score, validate_weight


class ScorerName(str, Enum):
    """Enumeration of ATS scorer algorithm names.

    These match the `name` field returned in ScorerResult.
    """

    TFIDF_COSINE = "tfidf_cosine"
    JACCARD_NGRAM = "jaccard_ngram"
    KEYWORD_EXACT = "keyword_exact"
    BERT_SEMANTIC = "bert_semantic"


class ScorerSelection(str, Enum):
    """CLI selection options for which scorer(s) to use.

    Used in the `screen` command's --scorers argument.
    """

    ALL = "all"
    TFIDF = "tfidf"
    JACCARD = "jaccard"
    KEYWORD = "keyword"
    BERT = "bert"


@dataclass
class ScorerResult:
    """Result from an ATS scoring algorithm.

    Attributes:
        name: Name of the scoring algorithm
        score: Raw score (must be in [0, 1])
        weight: Weight of this algorithm in tournament (must be in [0, 1])
        details: Additional algorithm-specific details
        component_scores: Breakdown of scores by component (all values in [0, 1])

    Raises:
        ValueError: If score, weight, or component_scores values are outside [0, 1]

    """

    name: str
    score: float
    weight: float = 1.0
    details: dict[str, Any] = field(default_factory=dict)
    component_scores: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate score and weight are in valid ranges."""
        validate_score(self.score, "score")
        validate_weight(self.weight, "weight")

        # Validate all component scores
        for key, value in self.component_scores.items():
            validate_score(value, f"component_scores[{key!r}]")

    @property
    def weighted_score(self) -> float:
        """Calculate weighted contribution to total score."""
        return self.score * self.weight

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "score": self.score,
            "weight": self.weight,
            "weighted_score": self.weighted_score,
            "details": self.details,
            "component_scores": self.component_scores,
        }


class BaseScorer(ABC):
    """Abstract base class for all ATS scoring algorithms.

    Each scorer implements a different approach to measuring resume-job
    compatibility (e.g., keyword matching, semantic similarity, etc.).
    """

    def __init__(self, weight: float = 1.0) -> None:
        """Initialize the scorer.

        Args:
            weight: Weight of this scorer in tournament (0-1). Default: 1.0

        Raises:
            ValueError: If weight is outside [0, 1]

        """
        validate_weight(weight, "weight")
        self.weight = weight

    @abstractmethod
    def score(
        self,
        resume_text: str,
        job_description: str,
        **kwargs: Any,
    ) -> ScorerResult:
        """Score a resume against a job description.

        Args:
            resume_text: Full text content of resume
            job_description: Full text content of job description
            **kwargs: Additional scorer-specific parameters

        Returns:
            ScorerResult with score and details

        """
        pass

    def _normalize_score(
        self,
        raw_score: float,
        min_val: float = 0.0,
        max_val: float = 1.0,
    ) -> float:
        """Normalize a score to [0, 1] range.

        Args:
            raw_score: Raw score value
            min_val: Expected minimum value
            max_val: Expected maximum value

        Returns:
            Normalized score in [0, 1]

        """
        if max_val == min_val:
            return 0.0
        normalized = (raw_score - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))


class DegreeType(str, Enum):
    """Enumeration of recognized educational degree types.

    Using str mixin allows direct comparison with strings and JSON serialization.
    See GitHub Issue #75 for design rationale.
    """

    ASSOCIATE = "Associate"
    BACHELOR = "Bachelor"
    MASTER = "Master"
    PHD = "PhD"
    CERTIFICATE = "Certificate"
    DIPLOMA = "Diploma"
    OTHER = "Other"  # Fallback for unrecognized degree types

    @classmethod
    def from_string(cls, value: str) -> DegreeType:
        """Convert a string to DegreeType, with fallback to OTHER.

        Args:
            value: String representation of degree type

        Returns:
            Matching DegreeType or OTHER if not recognized

        """
        # Normalize input
        normalized = value.strip().title()

        # Try direct match first
        for member in cls:
            if member.value == normalized:
                return member

        # Handle common aliases
        aliases = {
            "Phd": cls.PHD,
            "Doctorate": cls.PHD,
            "Doctor": cls.PHD,
            "Bs": cls.BACHELOR,
            "Ba": cls.BACHELOR,
            "Ms": cls.MASTER,
            "Ma": cls.MASTER,
            "Mba": cls.MASTER,
            "Aa": cls.ASSOCIATE,
            "As": cls.ASSOCIATE,
            "Cert": cls.CERTIFICATE,
        }
        return aliases.get(normalized, cls.OTHER)


@dataclass
class Degree:
    """Structured representation of an educational degree.

    Attributes:
        type: Type of degree (DegreeType enum or string for backwards compatibility)
        school: Name of the educational institution
        field: Field of study (e.g., "Computer Science"), optional

    Note:
        The type field accepts both DegreeType enum values and strings.
        Strings are automatically converted to DegreeType via from_string().

    """

    type: str | DegreeType
    school: str = "Unknown"
    field: str = ""

    def __post_init__(self) -> None:
        """Validate and normalize degree type."""
        if isinstance(self.type, str):
            # Convert string to DegreeType for validation/normalization
            self.type = DegreeType.from_string(self.type)
        if not self.type:
            raise ValueError("Degree type cannot be empty")

    @property
    def type_value(self) -> str:
        """Return the string value of the degree type."""
        if isinstance(self.type, DegreeType):
            return self.type.value
        return str(self.type)

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type_value,
            "school": self.school,
            "field": self.field,
        }


@dataclass
class ExtractedEntities:
    """Structured entities extracted from resume or job description.

    Attributes:
        skills: List of extracted skills
        experience_years: Total years of experience
        degrees: List of Degree objects
        certifications: List of certifications
        keywords: Important keywords (TF-IDF ranked)

    """

    skills: list[str] = field(default_factory=list)
    experience_years: float = 0.0
    degrees: list[Degree] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    keywords: list[tuple[str, float]] = field(default_factory=list)  # (word, tfidf)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "skills": self.skills,
            "experience_years": self.experience_years,
            "degrees": [d.to_dict() for d in self.degrees],
            "certifications": self.certifications,
            "keywords": [(k, v) for k, v in self.keywords],
        }
