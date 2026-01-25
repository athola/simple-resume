"""Entity extractor for resumes and job descriptions.

Extracts structured information from unstructured text:
- Skills (technical and soft skills)
- Experience years (from date ranges)
- Education (degrees, schools)
- Certifications

Uses pattern-based extraction for PoC, designed to be extensible
for NLP-based extraction (spaCy, transformers).

Architecture: Parse-once with lazy evaluation
------------------------------------------------
The ParsedDocument class caches common preprocessing (whitespace normalization,
sentence splitting) while allowing specialized patterns per extraction method.
This reduces redundant I/O and text processing when multiple extractors are used.

See GitHub Issue #60 for design rationale.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from re import Pattern

from sklearn.feature_extraction.text import TfidfVectorizer

from simple_resume.core.ats.base import Degree, ExtractedEntities
from simple_resume.core.ats.constants import MIN_CERTIFICATION_LENGTH, MIN_SKILL_LENGTH

logger = logging.getLogger(__name__)

# Common technical skills patterns (extensible)
TECH_SKILLS_PATTERNS = [
    r"\b(?:Python|JavaScript|TypeScript|Java|C\+\+|C#|Go|Rust|Ruby|PHP|Swift|Kotlin)\b",
    r"\b(?:React|Vue|Angular|Svelte|Next\.js|Nuxt\.js|Django|Flask|FastAPI|Spring|Express)\b",
    r"\b(?:SQL|NoSQL|MongoDB|PostgreSQL|MySQL|Redis|Elasticsearch|DynamoDB)\b",
    r"\b(?:AWS|Azure|GCP|Docker|Kubernetes|Terraform|Ansible|Jenkins)\b",
    r"\b(?:Git|GitHub|GitLab|Linux|Unix|Bash|Shell|PowerShell)\b",
    r"\b(?:TensorFlow|PyTorch|Keras|scikit-learn|pandas|numpy)\b",
    r"\b(?:HTML|CSS|SASS|REST|GraphQL|gRPC)\b",
]

# Combined pattern for all technical skills
TECH_SKILLS_PATTERN = re.compile("|".join(TECH_SKILLS_PATTERNS), re.IGNORECASE)


# Degree patterns
DEGREE_PATTERNS = [
    (r"(?:Bachelor'?s?|B\.S\.?|B\.A\.?|BS|BA)", "Bachelor"),
    (r"(?:Master'?s?|M\.S\.?|M\.A\.?|MS|MA|MBA|MBA)", "Master"),
    (r"(?:Ph\.?D\.?|Doctorate|Doctor)", "PhD"),
    (r"(?:Associate'?s?|A\.A\.?|A\.S\.?|AS|AA)", "Associate"),
]

# Field of study patterns
FIELD_PATTERNS = [
    r"(?:Computer\s+Science|CS|C\.S\.)",
    r"(?:Software\s+Engineering)",
    r"(?:Data\s+Science)",
    r"(?:Information\s+Technology|IT)",
    r"(?:Electrical\s+Engineering)",
    r"(?:Mechanical\s+Engineering)",
    r"(?:Business\s+Administration)",
    r"(?:Mathematics|Math)",
    r"(?:Physics)",
]

# Date patterns for experience calculation
DATE_FORMATS = [
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{4})",  # Jan 2020
    r"(\d{4})-(\d{2})",  # 2020-01
    r"(\d{4})",  # 2020
]

MONTH_MAP = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

# Date range pattern for experience extraction - compiled once at module level
# Matches patterns like "Jan 2020 - Present", "2020-01 - 2022-12", "2020 to 2022"
# See GitHub Issue #73 for rationale on module-level compilation.
DATE_RANGE_PATTERN: Pattern[str] = re.compile(
    r"""
    (?:^|[\n\*•\-\s]+)            # Line start or bullet
    [^\n]*?                       # Position title (non-greedy)
    (?:
        (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{4}) |
        (\d{4})-(\d{2}) |
        (\d{4})
    )
    \s*                          # Whitespace
    (?:to|–|-|\u2014|through)     # Separator variations
    \s*                          # Whitespace
    (?:
        (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{4}) |
        (\d{4})-(\d{2}) |
        (\d{4}) |
        (Present|Current|Now)
    )
    """,
    re.IGNORECASE | re.VERBOSE | re.MULTILINE,
)


def _parse_date(date_str: str) -> tuple[int, int] | None:
    """Parse a date string into (year, month) tuple.

    Args:
        date_str: Date string to parse

    Returns:
        (year, month) tuple or None if parsing fails

    """
    date_str = date_str.strip()

    # Try month year format (Jan 2020)
    month_year_pattern = (
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{4})"
    )
    match = re.match(month_year_pattern, date_str, re.IGNORECASE)
    if match:
        month_name = match.group(1).lower()
        year = int(match.group(2))
        month = MONTH_MAP.get(month_name, 1)
        return (year, month)

    # Try YYYY-MM format
    match = re.match(r"(\d{4})-(\d{2})", date_str)
    if match:
        return (int(match.group(1)), int(match.group(2)))

    # Try YYYY format
    match = re.match(r"(\d{4})", date_str)
    if match:
        return (int(match.group(1)), 1)

    return None


def _calculate_duration_years(
    start: tuple[int, int],
    end: tuple[int, int] | None,
) -> float:
    """Calculate duration between two dates in years.

    Args:
        start: (year, month) tuple for start date
        end: (year, month) tuple for end date, or None for "present"

    Returns:
        Duration in years (float)

    """
    if end is None:
        end_date = datetime.now()
        end_year, end_month = end_date.year, end_date.month
    else:
        end_year, end_month = end

    start_year, start_month = start

    years = end_year - start_year
    months = end_month - start_month

    return years + (months / 12.0)


class ParsedDocument:
    r"""Lazy-evaluated parsed document for efficient entity extraction.

    This class implements the parse-once architecture: common preprocessing
    is done once when first accessed, then cached for subsequent extractions.

    Each property is lazily evaluated using @cached_property, meaning:
    - `normalized_text` is computed once on first access
    - `sentences` uses `normalized_text` (only computed if needed)
    - `lines` uses `normalized_text` (only computed if needed)

    This allows specialized extractors to share preprocessing work while
    still using their own patterns for extraction.

    Attributes:
        raw_text: Original input text (immutable)

    Example:
        >>> doc = ParsedDocument("  Hello   World  \n\n  Test  ")
        >>> doc.normalized_text  # Computed on first access
        'Hello World\nTest'
        >>> doc.normalized_text  # Returns cached value

    """

    def __init__(self, text: str) -> None:
        """Initialize with raw text.

        Args:
            text: Raw input text to parse

        """
        self._raw_text = text

    @property
    def raw_text(self) -> str:
        """Return the original unmodified text."""
        return self._raw_text

    @cached_property
    def normalized_text(self) -> str:
        r"""Return whitespace-normalized text.

        Normalizes multiple spaces to single space, strips leading/trailing
        whitespace, and normalizes line endings to \n.
        """
        # Normalize line endings
        text = self._raw_text.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse multiple spaces (but preserve newlines)
        text = re.sub(r"[^\S\n]+", " ", text)
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split("\n")]
        # Collapse multiple blank lines
        result_lines = []
        prev_blank = False
        for line in lines:
            is_blank = not line
            if is_blank and prev_blank:
                continue
            result_lines.append(line)
            prev_blank = is_blank
        return "\n".join(result_lines).strip()

    @cached_property
    def lowercase_text(self) -> str:
        """Return lowercase normalized text for case-insensitive matching."""
        return self.normalized_text.lower()

    @cached_property
    def lines(self) -> list[str]:
        """Return non-empty lines from normalized text."""
        return [line for line in self.normalized_text.split("\n") if line]

    @cached_property
    def sentences(self) -> list[str]:
        """Return sentences split from normalized text.

        Uses simple sentence boundary detection (period followed by space/newline).
        """
        # Split on sentence boundaries (. followed by space or newline)
        raw_sentences = re.split(r"(?<=[.!?])\s+", self.normalized_text)
        return [s.strip() for s in raw_sentences if s.strip()]

    @cached_property
    def word_tokens(self) -> list[str]:
        """Return word tokens (alphabetic strings) from normalized text."""
        return re.findall(r"\b[A-Za-z]+\b", self.normalized_text)

    def find_section(self, header_pattern: str) -> str | None:
        """Find and return content of a section by header pattern.

        Args:
            header_pattern: Regex pattern to match section header

        Returns:
            Section content (text after header until next section), or None

        """
        pattern = rf"(?:{header_pattern})[\s:\n]+(.*?)(?=\n\n|\n[A-Z][a-z]+\s*:|\Z)"
        match = re.search(pattern, self.normalized_text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return None


def parse(text: str) -> ParsedDocument:
    """Parse text into a lazy-evaluated document.

    This is the main entry point for the parse-once architecture.
    Use this to create a ParsedDocument, then pass it to extractors.

    Args:
        text: Raw text to parse

    Returns:
        ParsedDocument with lazy-evaluated properties

    Example:
        >>> doc = parse("  Resume text here...  ")
        >>> doc.normalized_text  # Preprocessing done once
        >>> doc.lines  # Uses cached normalized_text

    """
    return ParsedDocument(text)


@dataclass
class EntityExtractor:
    """Extract structured entities from resume or job description text.

    Supports both raw strings and pre-parsed ParsedDocument objects.
    Using ParsedDocument enables the parse-once architecture for efficiency
    when extracting multiple entity types from the same text.

    Attributes:
        extract_keywords: Whether to extract TF-IDF keywords (requires sklearn)
        custom_skills: Optional custom skill patterns to add

    Example:
        # Option 1: Direct string (simple usage)
        extractor = EntityExtractor()
        entities = extractor.extract("Resume text here...")

        # Option 2: ParsedDocument (efficient for multiple extractions)
        doc = parse("Resume text here...")
        entities = extractor.extract(doc)

    """

    extract_keywords: bool = True
    custom_skills: list[str] = field(default_factory=list)
    custom_pattern: Pattern[str] | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Compile custom skill patterns."""
        if self.custom_skills:
            escaped_skills = [re.escape(skill) for skill in self.custom_skills]
            pattern = r"\b(?:{})\b".format("|".join(escaped_skills))
            self.custom_pattern = re.compile(pattern, re.IGNORECASE)
        else:
            self.custom_pattern = None

    def _ensure_parsed(self, text_or_doc: str | ParsedDocument) -> ParsedDocument:
        """Ensure input is a ParsedDocument.

        Args:
            text_or_doc: Either raw text string or ParsedDocument

        Returns:
            ParsedDocument (either passed through or newly created)

        """
        if isinstance(text_or_doc, ParsedDocument):
            return text_or_doc
        return ParsedDocument(text_or_doc)

    def extract(
        self,
        text: str | ParsedDocument,
        **kwargs: Any,  # noqa: ARG002
    ) -> ExtractedEntities:
        """Extract all entities from text.

        Args:
            text: Resume/job description text (str) or pre-parsed ParsedDocument
            **kwargs: Additional parameters (reserved for future use)

        Returns:
            ExtractedEntities with all extracted information

        Note:
            Pass a ParsedDocument when extracting from the same text multiple
            times to benefit from cached preprocessing (parse-once architecture).

        """
        doc = self._ensure_parsed(text)
        entities = ExtractedEntities()

        # Extract skills (uses normalized text for pattern matching)
        entities.skills = self._extract_skills(doc)

        # Calculate experience years (uses raw text for date patterns)
        entities.experience_years = self._calculate_experience(doc)

        # Extract education (uses section finding)
        entities.degrees = self._extract_education(doc)

        # Extract certifications (uses both patterns and sections)
        entities.certifications = self._extract_certifications(doc)

        # Extract keywords if requested (uses normalized text)
        if self.extract_keywords:
            entities.keywords = self._extract_keywords(doc)

        return entities

    def _extract_skills(self, doc: ParsedDocument) -> list[str]:
        """Extract technical skills from parsed document.

        Args:
            doc: ParsedDocument with cached normalized text

        Returns:
            List of unique skills found

        """
        skills_found = set()
        text = doc.normalized_text  # Use cached normalized text

        # Extract from predefined patterns
        for match in TECH_SKILLS_PATTERN.finditer(text):
            skills_found.add(match.group(0))

        # Extract from custom patterns
        if self.custom_pattern:
            for match in self.custom_pattern.finditer(text):
                skills_found.add(match.group(0))

        # Extract from skills section using ParsedDocument helper
        skills_section = doc.find_section(
            r"Skills|Technologies|Tech Stack|Core Competencies"
        )
        if skills_section:
            # Extract comma-separated, bullet, or dash-separated items
            items = re.split(r"[,\n•\-\*]", skills_section)
            for raw_item in items:
                item = raw_item.strip()
                # Only include if it looks like a skill (2+ chars, contains letters)
                if len(item) >= MIN_SKILL_LENGTH and re.search(r"[A-Za-z]", item):
                    skills_found.add(item)

        return sorted(skills_found, key=str.lower)

    def _calculate_experience(self, doc: ParsedDocument) -> float:
        """Calculate total years of experience from date ranges.

        Args:
            doc: ParsedDocument with cached text

        Returns:
            Total years of experience

        """
        total_years = 0.0
        # Use raw text for date patterns (preserves original formatting)
        text = doc.raw_text

        # Use module-level compiled pattern for performance
        for match in DATE_RANGE_PATTERN.finditer(text):
            groups = match.groups()

            # Groups structure:
            # 0: start_month (if Month YYYY format)
            # 1: start_year (if Month YYYY format)
            # 2: start_year-YYYY (if YYYY-MM format)
            # 3: start_year-MM (if YYYY-MM format)
            # 4: start_year (if YYYY only format)
            # 5: end_month (if Month YYYY format)
            # 6: end_year (if Month YYYY format)
            # 7: end_year-YYYY (if YYYY-MM format)
            # 8: end_year-MM (if YYYY-MM format)
            # 9: end_year (if YYYY only format)
            # 10: present/current/now keyword

            # Extract start date
            start_date = None
            if groups[0] and groups[1]:  # Month YYYY format
                start_date = _parse_date(f"{groups[0]} {groups[1]}")
            elif groups[2] and groups[3]:  # YYYY-MM format
                start_date = _parse_date(f"{groups[2]}-{groups[3]}")
            elif groups[4]:  # YYYY format
                start_date = _parse_date(groups[4])

            # Extract end date
            end_date = None
            if groups[10] and groups[10].lower() in ("present", "current", "now"):
                end_date = None  # Present
            elif groups[5] and groups[6]:  # Month YYYY format
                end_date = _parse_date(f"{groups[5]} {groups[6]}")
            elif groups[7] and groups[8]:  # YYYY-MM format
                end_date = _parse_date(f"{groups[7]}-{groups[8]}")
            elif groups[9]:  # YYYY format
                end_date = _parse_date(groups[9])

            if start_date:
                duration = _calculate_duration_years(start_date, end_date)
                total_years += duration

        # Also look for explicit "X years of experience" mentions
        explicit_pattern = re.search(
            r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s*(?:of\s*)?(?:experience|work)",
            text,
            re.IGNORECASE,
        )
        if explicit_pattern:
            explicit_years = float(explicit_pattern.group(1))
            # Use the max of calculated and explicit
            total_years = max(total_years, explicit_years)

        return round(total_years, 1)

    def _extract_education(self, doc: ParsedDocument) -> list[Degree]:
        """Extract education information (degrees, schools).

        Args:
            doc: ParsedDocument with section finding capability

        Returns:
            List of Degree objects

        """
        degrees: list[Degree] = []

        # Use ParsedDocument's section finding (cached normalized text)
        section_text = doc.find_section(r"Education|Academic|Degree")

        if section_text:
            # Find degree mentions
            for pattern, degree_type in DEGREE_PATTERNS:
                matches = re.finditer(pattern, section_text, re.IGNORECASE)
                for match in matches:
                    # Try to extract surrounding context (school, field)
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(section_text), match.end() + 100)
                    context = section_text[context_start:context_end]

                    # Extract field of study if present
                    field = None
                    for field_pattern in FIELD_PATTERNS:
                        field_match = re.search(field_pattern, context, re.IGNORECASE)
                        if field_match:
                            field = field_match.group(0)
                            break

                    # Try to extract school name (usually before degree)
                    school_pattern = r"([A-Z][A-Za-z\s&]+?)(?:,|\n|" + pattern + r")"
                    school_match = re.search(school_pattern, context)
                    if school_match:
                        school = school_match.group(1).strip()
                    else:
                        school = "Unknown"

                    degrees.append(
                        Degree(
                            type=degree_type,
                            school=school,
                            field=field or "",
                        )
                    )

        return degrees

    def _extract_certifications(self, doc: ParsedDocument) -> list[str]:
        """Extract certifications from parsed document.

        Args:
            doc: ParsedDocument with cached normalized text

        Returns:
            List of certification names

        """
        certifications = []
        text = doc.normalized_text  # Use cached normalized text

        # Common certification patterns
        cert_patterns = [
            r"(?:AWS|Amazon)\s+(?:Certified\s+)?(?:Solutions?\s+Architect|Developer|SysOps)\s+(?:Associate|Professional)",
            r"(?:Google\s+)?(?:Cloud\s+)?Certified",
            r"(?:Microsoft\s+)?Azure\s+(?:Certified\s+)?\w+",
            r"Cisco\s+(?:CCNA|CCNP|CCIE)",
            r"(?:CompTIA\s+)?(?:A\+|Network\+|Security\+)",
            r"PMP",
            r"Scrum\s+Master",
            r"Six\s+Sigma",
            r"(?: Certified\s+)?(?:Kubernetes|CKA|CKAD)",
            r"(?:Oracle|Java)\s+Certified",
        ]

        combined_pattern = "|".join(f"(?:{pattern})" for pattern in cert_patterns)
        cert_regex = re.compile(combined_pattern, re.IGNORECASE)

        for match in cert_regex.finditer(text):
            certifications.append(match.group(0).strip())

        # Also look for explicit "Certification:" sections using ParsedDocument
        cert_section = doc.find_section(r"Certifications?|Certificates?|Credentials?")
        if cert_section:
            # Extract line-by-line
            for raw_line in cert_section.split("\n"):
                line = raw_line.strip()
                if line and len(line) > MIN_CERTIFICATION_LENGTH:
                    certifications.append(line)

        return list(set(certifications))  # Deduplicate

    def _extract_keywords(self, doc: ParsedDocument) -> list[tuple[str, float]]:
        """Extract important keywords using TF-IDF.

        Args:
            doc: ParsedDocument with cached normalized text

        Returns:
            List of (keyword, tfidf_score) tuples

        """
        text = doc.normalized_text  # Use cached normalized text
        # Simple TF-IDF for single document (returns raw term frequencies)
        try:
            vectorizer = TfidfVectorizer(
                max_features=50,
                ngram_range=(1, 2),
                stop_words="english",
                lowercase=True,
            )
            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            tfidf_scores = tfidf_matrix.toarray()[0]

            # Get non-zero keywords
            keywords = [
                (feature_names[i], float(tfidf_scores[i]))
                for i in range(len(feature_names))
                if tfidf_scores[i] > 0
            ]

            # Sort by TF-IDF score
            keywords.sort(key=lambda x: x[1], reverse=True)
            return keywords[:20]  # Top 20 keywords

        except ValueError as e:
            # Sklearn error (e.g., empty after stopword filtering)
            logger.warning(
                "TF-IDF keyword extraction failed: %s. Returning empty keywords.",
                str(e),
            )
            return []


def extract_entities(
    text: str | ParsedDocument,
    **kwargs: Any,
) -> ExtractedEntities:
    """Extract entities from text or parsed document.

    Args:
        text: Resume/job description text (str) or pre-parsed ParsedDocument
        **kwargs: Additional parameters for EntityExtractor

    Returns:
        ExtractedEntities with all extracted information

    Example:
        # Simple usage with string
        entities = extract_entities("Resume text here...")

        # Efficient usage with ParsedDocument
        doc = parse("Resume text here...")
        entities = extract_entities(doc)

    """
    extractor = EntityExtractor(**kwargs)
    return extractor.extract(text)
