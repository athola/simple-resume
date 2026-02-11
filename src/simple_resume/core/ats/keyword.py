"""Exact keyword match scorer with fuzzy tolerance.

This scorer performs direct keyword matching between resume and job description:
- Exact word/phrase matching
- Fuzzy matching for spelling variations (using SequenceMatcher)
- Configurable keyword extraction from job descriptions

This is the most traditional ATS approach, simulating how older
systems filter resumes based on keyword presence.

Pros:
- Fast and simple
- Easy to understand and explain
- Good for hard requirements (e.g., specific technologies)

Cons:
- Misses semantic variations
- Penalizes creative language
- Vulnerable to keyword stuffing
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from simple_resume.core.ats.base import BaseScorer, ScorerResult
from simple_resume.core.ats.constants import (
    CRITICAL_KEYWORDS_THRESHOLD,
    MIN_FALLBACK_WORD_LENGTH,
    MIN_KEYWORD_LENGTH,
    validate_threshold,
)
from simple_resume.core.ats.creative_terms import (
    Industry,
    expand_term,
    is_creative_term,
)


@dataclass(frozen=True)
class KeywordScorerConfig:
    """Configuration for keyword scoring behavior.

    Attributes:
        fuzzy_threshold: Minimum similarity ratio for fuzzy matching (0-1)
        case_sensitive: Whether matching preserves case
        extract_keywords: Whether to auto-extract keywords from job text
        max_keywords: Cap on keywords extracted from job description
        enable_creative_expansion: Expand creative synonyms during matching
        industry: Industry context for creative term mappings

    """

    fuzzy_threshold: float = 0.85
    case_sensitive: bool = False
    extract_keywords: bool = True
    max_keywords: int = 50
    enable_creative_expansion: bool = False
    industry: Industry = Industry.GENERAL

    def __post_init__(self) -> None:
        """Validate configuration values."""
        validate_threshold(self.fuzzy_threshold, "fuzzy_threshold")


class KeywordScorer(BaseScorer):
    """Exact keyword match scorer with fuzzy tolerance.

    Performs direct keyword matching between resume and job description.
    Supports exact matching, fuzzy matching for typos, and configurable
    keyword extraction.
    """

    def __init__(
        self,
        weight: float = 1.0,
        config: KeywordScorerConfig | None = None,
    ) -> None:
        """Initialize keyword scorer.

        Args:
            weight: Weight in tournament (default: 1.0, must be in [0, 1])
            config: Scoring configuration (uses defaults if None)

        Raises:
            ValueError: If weight is outside [0, 1]

        """
        super().__init__(weight=weight)
        self._config = config or KeywordScorerConfig()
        self.fuzzy_threshold = self._config.fuzzy_threshold
        self.case_sensitive = self._config.case_sensitive
        self.extract_keywords = self._config.extract_keywords
        self.max_keywords = self._config.max_keywords
        self.enable_creative_expansion = self._config.enable_creative_expansion
        self.industry = self._config.industry

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for keyword matching.

        Args:
            text: Raw text input

        Returns:
            Cleaned text

        """
        if not self.case_sensitive:
            text = text.lower()
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_keywords(
        self, text: str, original_text: str | None = None
    ) -> list[str]:
        """Extract important keywords from text.

        Uses simple heuristics to identify likely keywords:
        - Technical terms (capitalized words, acronyms)
        - Skills (common patterns)
        - Experience phrases
        - Nouns and technical terms (fallback extraction)

        Args:
            text: Preprocessed text
            original_text: Original text before preprocessing (for case-sensitive
                pattern matching). Falls back to text if not provided.

        Returns:
            List of extracted keywords

        """
        keywords = []

        # Use original text for case-sensitive pattern matching
        if original_text is None:
            original_text = text

        # Extract technical terms (words with internal caps, acronyms)
        # Pattern: CamelCase, ALL_CAPS, words with numbers
        technical_pattern = r"\b[A-Z]{2,}\b|\b[A-Z][a-z]+[A-Z][a-z]+\b|\b\w*\d\w*\b"
        technical_matches = re.findall(technical_pattern, original_text)
        keywords.extend(technical_matches)

        # Extract phrases in quotes (often important skills/technologies)
        quote_pattern = r'"([^"]+)"'
        quote_matches = re.findall(quote_pattern, original_text)
        keywords.extend(quote_matches)

        # Common skill/technology patterns
        # Words with 3+ consecutive consonants or specific patterns
        skill_pattern = (
            r"\b[A-Za-z]{3,}\s?(?:framework|library|language|platform|tool|database)\b"
        )
        skill_matches = re.findall(skill_pattern, original_text, re.IGNORECASE)
        keywords.extend(skill_matches)

        # Extract capitalized words (proper nouns, technologies like Python, Java)
        # This catches single-word technologies that aren't acronyms
        capitalized_pattern = r"\b[A-Z][a-z]{2,}\b"
        capitalized_matches = re.findall(capitalized_pattern, original_text)
        keywords.extend(capitalized_matches)

        # Fallback: if no keywords found, extract significant words
        # (nouns/technical terms typically 4+ chars, not common stopwords)
        if not keywords:
            stopwords = {
                "the",
                "and",
                "for",
                "are",
                "but",
                "not",
                "you",
                "all",
                "can",
                "had",
                "her",
                "was",
                "one",
                "our",
                "out",
                "has",
                "have",
                "been",
                "were",
                "being",
                "will",
                "with",
                "this",
                "that",
                "from",
                "they",
                "would",
                "there",
                "their",
                "what",
                "about",
                "which",
                "when",
                "make",
                "like",
                "just",
                "over",
                "such",
                "into",
                "than",
                "them",
                "some",
                "could",
                "other",
                "experience",
                "work",
                "working",
                "team",
                "ability",
            }
            words = text.split()
            for word in words:
                word_clean = re.sub(r"[^\w]", "", word)
                if (
                    len(word_clean) >= MIN_FALLBACK_WORD_LENGTH
                    and word_clean.lower() not in stopwords
                    and not word_clean.isdigit()
                ):
                    keywords.append(word_clean)

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            kw_clean = kw.strip().lower()
            if kw_clean and len(kw_clean) > MIN_KEYWORD_LENGTH and kw_clean not in seen:
                seen.add(kw_clean)
                unique_keywords.append(kw.strip())

        return unique_keywords[: self.max_keywords]

    def _fuzzy_match(
        self,
        keyword: str,
        text: str,
    ) -> tuple[bool, float]:
        """Perform fuzzy matching for a keyword against text.

        Uses SequenceMatcher for robust similarity calculation.

        Args:
            keyword: Keyword to find
            text: Text to search in

        Returns:
            (found, similarity_score)

        """
        # Direct match
        if keyword in text:
            return True, 1.0

        # Word boundary match
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(pattern, text, re.IGNORECASE if not self.case_sensitive else 0):
            return True, 1.0

        # Fuzzy matching using SequenceMatcher
        # Check similarity with each word in text
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        words = text_lower.split()

        best_similarity = 0.0
        for word in words:
            # Use SequenceMatcher for proper fuzzy matching
            matcher = SequenceMatcher(None, keyword_lower, word, autojunk=False)
            similarity = matcher.ratio()
            best_similarity = max(best_similarity, similarity)

        return best_similarity >= self.fuzzy_threshold, best_similarity

    def _expand_creative_terms(
        self, keywords: list[str]
    ) -> tuple[set[str], list[dict[str, str]]]:
        """Build expanded keyword set from creative term synonyms.

        Args:
            keywords: Original keywords to expand

        Returns:
            Tuple of (expanded_keywords set, creative_terms_found list)

        """
        expanded: set[str] = set()
        found: list[dict[str, str]] = []
        if not self.enable_creative_expansion:
            return expanded, found
        for keyword in keywords:
            if is_creative_term(keyword, self.industry):
                synonym = expand_term(keyword, self.industry)
                if synonym:
                    found.append({"creative": keyword, "expanded": synonym})
                    expanded.add(synonym)
        return expanded, found

    def score(
        self,
        resume_text: str,
        job_description: str,
        **kwargs: Any,
    ) -> ScorerResult:
        """Score resume against job description using exact keyword matching.

        Args:
            resume_text: Full resume text
            job_description: Full job description text
            **kwargs: Additional parameters including:
                - keywords: Optional list of specific keywords to match

        Returns:
            ScorerResult with keyword match score and details

        """
        # Handle edge cases
        if not resume_text.strip() or not job_description.strip():
            return ScorerResult(
                name="keyword_exact",
                score=0.0,
                weight=self.weight,
                details={
                    "exact_matches": 0,
                    "total_keywords": 0,
                    "matched_keywords": [],
                    "missing_keywords": [],
                    "creative_terms_expanded": [],
                    "error": "Empty input provided",
                },
            )

        # Preprocess texts (save originals for case-sensitive pattern matching)
        resume_clean = self._preprocess_text(resume_text)
        job_clean = self._preprocess_text(job_description)

        # Get keywords to match (either provided or extracted)
        keywords = kwargs.get("keywords")
        if keywords is None and self.extract_keywords:
            keywords = self._extract_keywords(job_clean, original_text=job_description)
        elif keywords is None:
            # Use all unique words from job as keywords
            keywords = list(set(job_clean.split()))

        if not keywords:
            return ScorerResult(
                name="keyword_exact",
                score=0.0,
                weight=self.weight,
                details={
                    "exact_matches": 0,
                    "fuzzy_matches": 0,
                    "total_keywords": 0,
                    "matched_keywords": [],
                    "fuzzy_matched": [],
                    "missing_keywords": [],
                    "creative_terms_expanded": [],
                    "error": "No keywords to match",
                },
            )

        # Match keywords against resume
        matched_keywords = []
        missing_keywords = []
        fuzzy_matches = []

        # Work on a copy to avoid mutating the caller's list
        keywords = list(keywords)

        # Expand creative terms into additional match candidates
        expanded_keywords, creative_terms_found = self._expand_creative_terms(keywords)

        # Track original keyword count before adding expansions
        total_keywords = len(keywords)

        # Match original keywords plus expanded terms against resume
        all_match_terms = keywords + list(expanded_keywords)

        for keyword in all_match_terms:
            keyword_clean = keyword if self.case_sensitive else keyword.lower()
            found, similarity = self._fuzzy_match(keyword_clean, resume_clean)

            if found:
                if similarity >= 1.0:
                    matched_keywords.append(keyword)
                else:
                    fuzzy_matches.append((keyword, float(similarity)))
            else:
                missing_keywords.append(keyword)

        # Calculate score (total_keywords based on original keywords, not expanded)
        exact_match_count = len(matched_keywords)
        fuzzy_match_count = len(fuzzy_matches)

        # Weight exact matches higher than fuzzy matches
        exact_score = exact_match_count / total_keywords if total_keywords > 0 else 0.0
        fuzzy_bonus = (
            fuzzy_match_count / total_keywords * 0.5 if total_keywords > 0 else 0.0
        )

        overall_score = exact_score + fuzzy_bonus
        overall_score = min(1.0, overall_score)  # Cap at 1.0

        # Calculate component scores
        component_scores = {
            "exact_match_rate": exact_score,
            "fuzzy_match_rate": (
                fuzzy_match_count / total_keywords if total_keywords > 0 else 0.0
            ),
            "critical_keywords_present": (
                1.0
                if exact_match_count >= (total_keywords * CRITICAL_KEYWORDS_THRESHOLD)
                else 0.0
            ),
        }

        return ScorerResult(
            name="keyword_exact",
            score=overall_score,
            weight=self.weight,
            details={
                "exact_matches": exact_match_count,
                "fuzzy_matches": fuzzy_match_count,
                "total_keywords": total_keywords,
                "matched_keywords": matched_keywords,
                "fuzzy_matched": fuzzy_matches,
                "missing_keywords": missing_keywords,
                "match_rate": overall_score,
                "creative_terms_expanded": creative_terms_found,
            },
            component_scores=component_scores,
        )
