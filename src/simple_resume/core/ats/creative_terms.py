"""Creative language term mappings and synonym expansion.

This module provides support for detecting and normalizing creative/non-standard
resume language to professional terminology. It enables the system to handle
expressive language while still providing accurate ATS-style scoring.

Features:
- Synonym expansion (rockstar developer → senior developer)
- Industry-specific dictionaries (tech, enterprise, creative)
- Confidence scoring for uncertain term matches
- Term normalization for consistent matching

See GitHub Issue #62 for design rationale.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from re import sub


class Industry(str, Enum):
    """Industry types for specialized terminology."""

    GENERAL = "general"
    TECH = "tech"
    ENTERPRISE = "enterprise"
    CREATIVE = "creative"


@dataclass(frozen=True)
class CreativeTerm:
    """A creative term with its professional equivalent.

    Attributes:
        creative: The non-standard creative term
        professional: The professional equivalent
        confidence: Confidence level of this mapping (low/medium/high)
        industry: Industry this term applies to (default: GENERAL)

    """

    creative: str
    professional: str
    confidence: str
    industry: Industry = Industry.GENERAL


# Core creative term mappings (GENERAL dictionary)
_GENERAL_TERMS: list[CreativeTerm] = [
    # Developer titles
    CreativeTerm(
        creative="rockstar developer",
        professional="senior developer",
        confidence="low",
    ),
    CreativeTerm(
        creative="ninja coder",
        professional="expert programmer",
        confidence="low",
    ),
    CreativeTerm(
        creative="code ninja",
        professional="expert programmer",
        confidence="low",
    ),
    CreativeTerm(
        creative="dev guru",
        professional="senior developer",
        confidence="low",
    ),
    CreativeTerm(
        creative="programming wizard",
        professional="expert software engineer",
        confidence="low",
    ),
    # Marketing terms
    CreativeTerm(
        creative="growth hacker",
        professional="marketing specialist",
        confidence="medium",
    ),
    CreativeTerm(
        creative="brand evangelist",
        professional="brand manager",
        confidence="medium",
    ),
    CreativeTerm(
        creative="social media ninja",
        professional="social media manager",
        confidence="low",
    ),
    # General creative terms
    CreativeTerm(
        creative="rockstar",
        professional="expert",
        confidence="low",
    ),
    CreativeTerm(
        creative="ninja",
        professional="expert",
        confidence="low",
    ),
    CreativeTerm(
        creative="guru",
        professional="expert",
        confidence="low",
    ),
    CreativeTerm(
        creative="wizard",
        professional="expert",
        confidence="low",
    ),
    CreativeTerm(
        creative="ninja",
        professional="expert",
        confidence="low",
    ),
]


# Tech startup industry dictionary (more permissive of creative language)
_TECH_TERMS: list[CreativeTerm] = [
    *_GENERAL_TERMS,
    # Tech-specific creative terms
    CreativeTerm(
        creative="full stack rockstar",
        professional="full stack developer",
        confidence="low",
        industry=Industry.TECH,
    ),
    CreativeTerm(
        creative="backend ninja",
        professional="backend developer",
        confidence="low",
        industry=Industry.TECH,
    ),
    CreativeTerm(
        creative="frontend wizard",
        professional="frontend developer",
        confidence="low",
        industry=Industry.TECH,
    ),
]


# Enterprise industry dictionary (stricter, more formal)
_ENTERPRISE_TERMS: list[CreativeTerm] = [
    *_GENERAL_TERMS,
    # Enterprise mappings to formal titles
    CreativeTerm(
        creative="tech lead",
        professional="engineering manager",
        confidence="medium",
        industry=Industry.ENTERPRISE,
    ),
    CreativeTerm(
        creative="team lead",
        professional="engineering manager",
        confidence="high",
        industry=Industry.ENTERPRISE,
    ),
]


# Creative industry dictionary (allows more expression)
_CREATIVE_TERMS: list[CreativeTerm] = [
    *_GENERAL_TERMS,
    # Creative industry specific
    CreativeTerm(
        creative="creative technologist",
        professional="developer",
        confidence="high",
        industry=Industry.CREATIVE,
    ),
    CreativeTerm(
        creative="design engineer",
        professional="frontend developer",
        confidence="medium",
        industry=Industry.CREATIVE,
    ),
]


def get_industry_dictionary(
    industry: Industry = Industry.GENERAL,
) -> list[CreativeTerm]:
    """Get creative term dictionary for a specific industry.

    Args:
        industry: The industry type (default: GENERAL)

    Returns:
        List of CreativeTerm mappings for the industry

    """
    dictionaries = {
        Industry.GENERAL: _GENERAL_TERMS,
        Industry.TECH: _TECH_TERMS,
        Industry.ENTERPRISE: _ENTERPRISE_TERMS,
        Industry.CREATIVE: _CREATIVE_TERMS,
    }
    return dictionaries.get(industry, _GENERAL_TERMS)


def normalize_term(term: str) -> str:
    """Normalize a term for consistent matching.

    Args:
        term: The term to normalize

    Returns:
        Normalized term (lowercase, trimmed)

    """
    return sub(r"\s+", " ", term.strip().lower())


def is_creative_term(term: str, industry: Industry = Industry.GENERAL) -> bool:
    """Check if a term is a known creative/non-standard term.

    Args:
        term: The term to check
        industry: Industry context for lookup

    Returns:
        True if the term is a known creative term

    """
    normalized = normalize_term(term)
    dictionary = get_industry_dictionary(industry)

    return any(normalize_term(mapping.creative) == normalized for mapping in dictionary)


def expand_term(term: str, industry: Industry = Industry.GENERAL) -> str | None:
    """Expand a creative term to its professional equivalent.

    Args:
        term: The creative term to expand
        industry: Industry context for lookup

    Returns:
        Professional equivalent if found, None otherwise

    """
    normalized = normalize_term(term)
    dictionary = get_industry_dictionary(industry)

    for mapping in dictionary:
        if normalize_term(mapping.creative) == normalized:
            return mapping.professional

    return None


__all__ = [
    "CreativeTerm",
    "Industry",
    "normalize_term",
    "is_creative_term",
    "expand_term",
    "get_industry_dictionary",
]
