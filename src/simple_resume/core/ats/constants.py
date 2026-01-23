"""Constants for ATS scoring algorithms.

This module centralizes all magic numbers, thresholds, and configuration
defaults used across the ATS scoring system. Having a single source of
truth prevents value drift between components and improves maintainability.
"""

from __future__ import annotations

from enum import Enum
from typing import Final

# =============================================================================
# Score Classification Thresholds (0-100 scale)
# =============================================================================

# Score thresholds for status labels (Excellent/Good/Fair/Poor/Very Poor)
SCORE_EXCELLENT_THRESHOLD: Final[int] = 80
SCORE_GOOD_THRESHOLD: Final[int] = 65
SCORE_FAIR_THRESHOLD: Final[int] = 50
SCORE_POOR_THRESHOLD: Final[int] = 35

# Priority thresholds for improvement recommendations
PRIORITY_LOW_THRESHOLD: Final[int] = 70
PRIORITY_MEDIUM_THRESHOLD: Final[int] = 50

# =============================================================================
# Default Scorer Weights (must sum to 1.0 for normalization)
# =============================================================================

# Weights when BERT is available (semantic understanding gets highest weight)
DEFAULT_BERT_WEIGHT: Final[float] = 0.35
DEFAULT_TFIDF_WEIGHT: Final[float] = 0.30
DEFAULT_JACCARD_WEIGHT: Final[float] = 0.20
DEFAULT_KEYWORD_WEIGHT: Final[float] = 0.15

# Weights when BERT is unavailable (redistributed to statistical scorers)
FALLBACK_TFIDF_WEIGHT: Final[float] = 0.40
FALLBACK_JACCARD_WEIGHT: Final[float] = 0.30
FALLBACK_KEYWORD_WEIGHT: Final[float] = 0.30

# =============================================================================
# TF-IDF Scorer Constants
# =============================================================================

# Maximum keywords to extract from each document
TOP_KEYWORDS_LIMIT: Final[int] = 20

# Normalization divisor for experience relevance score.
# Empirically, shared TF-IDF products rarely exceed 10.0 even for long documents.
EXPERIENCE_RELEVANCE_NORMALIZER: Final[float] = 10.0

# Default vectorizer settings
DEFAULT_TFIDF_MAX_FEATURES: Final[int] = 1000
DEFAULT_TFIDF_NGRAM_RANGE: Final[tuple[int, int]] = (1, 2)
DEFAULT_TFIDF_MIN_DF: Final[int] = 1
DEFAULT_TFIDF_MAX_DF: Final[float] = 0.9

# =============================================================================
# Jaccard Scorer Constants
# =============================================================================

# N-gram range for phrase matching (1=unigrams, 2=bigrams, 3=trigrams)
DEFAULT_JACCARD_NGRAM_RANGE: Final[tuple[int, int]] = (1, 3)

# Maximum shared n-grams to include in results
MAX_SHARED_NGRAMS: Final[int] = 50

# Threshold for phrase match bonus calculation
PHRASE_MATCH_BONUS_THRESHOLD: Final[float] = 0.5

# =============================================================================
# Keyword Scorer Constants
# =============================================================================

# Minimum length for extracted keywords
MIN_KEYWORD_LENGTH: Final[int] = 2

# Default fuzzy matching threshold (0.85 = 85% similarity required)
DEFAULT_FUZZY_THRESHOLD: Final[float] = 0.85

# Maximum keywords to extract from job description
DEFAULT_MAX_KEYWORDS: Final[int] = 50

# Threshold for "critical keywords present" component score
CRITICAL_KEYWORDS_THRESHOLD: Final[float] = 0.5

# =============================================================================
# Entity Extraction Constants
# =============================================================================

# Minimum character length for extracted skills
MIN_SKILL_LENGTH: Final[int] = 2

# Minimum character length for extracted certifications
MIN_CERTIFICATION_LENGTH: Final[int] = 3

# =============================================================================
# Report Generation Constants
# =============================================================================

# Maximum missing keywords to include in recommendations
MAX_MISSING_KEYWORDS: Final[int] = 10

# Jaccard threshold below which phrasing recommendations are made
JACCARD_RECOMMENDATION_THRESHOLD: Final[float] = 0.5

# Component weights for report scoring
COMPONENT_WEIGHT_EXPERIENCE: Final[float] = 0.35
COMPONENT_WEIGHT_SKILLS: Final[float] = 0.25
COMPONENT_WEIGHT_SEMANTIC: Final[float] = 0.15
COMPONENT_WEIGHT_KEYWORDS: Final[float] = 0.10
COMPONENT_WEIGHT_EDUCATION: Final[float] = 0.10
COMPONENT_WEIGHT_FORMAT: Final[float] = 0.05

# =============================================================================
# Tournament Constants
# =============================================================================

# Default preview length for resume text snippets in batch screening
DEFAULT_PREVIEW_LENGTH: Final[int] = 100

# =============================================================================
# Validation Constants
# =============================================================================


class ScoreRange(Enum):
    """Valid score range for all scorers."""

    MIN = 0.0
    MAX = 1.0


class WeightRange(Enum):
    """Valid weight range for scorer weights."""

    MIN = 0.0
    MAX = 1.0


# Validation helper functions
def validate_score(score: float, name: str = "score") -> None:
    """Validate that a score is in the valid range [0, 1].

    Args:
        score: Score value to validate
        name: Name of the score for error messages

    Raises:
        ValueError: If score is outside [0, 1]

    """
    if not ScoreRange.MIN.value <= score <= ScoreRange.MAX.value:
        raise ValueError(
            f"{name} must be in [{ScoreRange.MIN.value}, {ScoreRange.MAX.value}], "
            f"got {score}"
        )


def validate_weight(weight: float, name: str = "weight") -> None:
    """Validate that a weight is in the valid range [0, 1].

    Args:
        weight: Weight value to validate
        name: Name of the weight for error messages

    Raises:
        ValueError: If weight is outside [0, 1]

    """
    if not WeightRange.MIN.value <= weight <= WeightRange.MAX.value:
        raise ValueError(
            f"{name} must be in [{WeightRange.MIN.value}, {WeightRange.MAX.value}], "
            f"got {weight}"
        )


def validate_ngram_range(
    ngram_range: tuple[int, int], name: str = "ngram_range"
) -> None:
    """Validate n-gram range configuration.

    Args:
        ngram_range: Tuple of (min_n, max_n) for n-gram generation
        name: Name of the parameter for error messages

    Raises:
        ValueError: If values are not positive integers or min > max

    """
    min_n, max_n = ngram_range
    if min_n < 1:
        raise ValueError(f"{name} min must be >= 1, got {min_n}")
    if max_n < 1:
        raise ValueError(f"{name} max must be >= 1, got {max_n}")
    if min_n > max_n:
        raise ValueError(f"{name} min ({min_n}) must be <= max ({max_n})")


def validate_threshold(
    threshold: float,
    name: str = "threshold",
    min_val: float = 0.0,
    max_val: float = 1.0,
) -> None:
    """Validate that a threshold is in valid range.

    Args:
        threshold: Threshold value to validate
        name: Name of the parameter for error messages
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)

    Raises:
        ValueError: If threshold is outside [min_val, max_val]

    """
    if not min_val <= threshold <= max_val:
        raise ValueError(f"{name} must be in [{min_val}, {max_val}], got {threshold}")
