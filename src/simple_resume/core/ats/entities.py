"""Entity extractor for resumes and job descriptions.

Extracts structured information from unstructured text:
- Skills (technical and soft skills)
- Experience years (from date ranges)
- Education (degrees, schools)
- Certifications

Uses pattern-based extraction for PoC, designed to be extensible
for NLP-based extraction (spaCy, transformers).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from re import Pattern

from sklearn.feature_extraction.text import TfidfVectorizer

from simple_resume.core.ats.base import ExtractedEntities

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


@dataclass
class EntityExtractor:
    """Extract structured entities from resume or job description text.

    Attributes:
        extract_keywords: Whether to extract TF-IDF keywords (requires sklearn)
        custom_skills: Optional custom skill patterns to add

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

    def extract(
        self,
        text: str,
        **kwargs: Any,
    ) -> ExtractedEntities:
        """Extract all entities from text.

        Args:
            text: Resume or job description text
            **kwargs: Additional parameters

        Returns:
            ExtractedEntities with all extracted information

        """
        entities = ExtractedEntities()

        # Extract skills
        entities.skills = self._extract_skills(text)

        # Calculate experience years
        entities.experience_years = self._calculate_experience(text)

        # Extract education
        entities.degrees = self._extract_education(text)

        # Extract certifications
        entities.certifications = self._extract_certifications(text)

        # Extract keywords if requested
        if self.extract_keywords:
            entities.keywords = self._extract_keywords(text)

        return entities

    def _extract_skills(self, text: str) -> list[str]:
        """Extract technical skills from text.

        Args:
            text: Resume or job description text

        Returns:
            List of unique skills found

        """
        skills_found = set()

        # Extract from predefined patterns
        for match in TECH_SKILLS_PATTERN.finditer(text):
            skills_found.add(match.group(0))

        # Extract from custom patterns
        if self.custom_pattern:
            for match in self.custom_pattern.finditer(text):
                skills_found.add(match.group(0))

        # Extract from common skill section patterns
        # Look for "Skills:" sections and extract items
        skills_pattern = (
            r"(?:Skills|Technologies|Tech Stack|Core Competencies)[:\s]+"
            r"(.*?)(?=\n\n|\n[A-Z]|\Z)"
        )
        skills_section = re.search(skills_pattern, text, re.IGNORECASE | re.DOTALL)
        if skills_section:
            section_text = skills_section.group(1)
            # Extract comma-separated, bullet, or dash-separated items
            items = re.split(r"[,\n•\-\*]", section_text)
            MIN_SKILL_LENGTH = 2
            for raw_item in items:
                item = raw_item.strip()
                # Only include if it looks like a skill (2+ chars, contains letters)
                if len(item) >= MIN_SKILL_LENGTH and re.search(r"[A-Za-z]", item):
                    skills_found.add(item)

        return sorted(skills_found, key=str.lower)

    def _calculate_experience(self, text: str) -> float:
        """Calculate total years of experience from date ranges.

        Args:
            text: Resume or job description text

        Returns:
            Total years of experience

        """
        total_years = 0.0

        # Look for date range patterns like "Jan 2020 - Present" or "2020-01 - 2022-12"
        # This handles various formats
        date_range_pattern = re.compile(
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

        for match in date_range_pattern.finditer(text):
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

    def _extract_education(self, text: str) -> list[dict[str, str]]:
        """Extract education information (degrees, schools).

        Args:
            text: Resume or job description text

        Returns:
            List of degree dictionaries

        """
        degrees = []

        # Look for education section
        education_section = re.search(
            r"(?:Education|Academic|Degree)[\s:\n]+(.*?)(?=\n\n|\n[A-Z][a-z]+\s*:|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if education_section:
            section_text = education_section.group(1)

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
                        {
                            "type": degree_type,
                            "school": school,
                            "field": field or "",
                        }
                    )

        return degrees

    def _extract_certifications(self, text: str) -> list[str]:
        """Extract certifications from text.

        Args:
            text: Resume or job description text

        Returns:
            List of certification names

        """
        certifications = []

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

        # Also look for explicit "Certification:" sections
        cert_section = re.search(
            r"(?:Certifications?|Certificates?|Credentials?)[\s:\n]+(.*?)(?=\n\n|\n[A-Z][a-z]+\s*:|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if cert_section:
            section_text = cert_section.group(1)
            # Extract line-by-line
            MIN_CERT_LENGTH = 3
            for raw_line in section_text.split("\n"):
                line = raw_line.strip()
                if line and len(line) > MIN_CERT_LENGTH:
                    certifications.append(line)

        return list(set(certifications))  # Deduplicate

    def _extract_keywords(self, text: str) -> list[tuple[str, float]]:
        """Extract important keywords using TF-IDF.

        Args:
            text: Resume or job description text

        Returns:
            List of (keyword, tfidf_score) tuples

        """
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
    text: str,
    **kwargs: Any,
) -> ExtractedEntities:
    """Extract entities from text.

    Args:
        text: Resume or job description text
        **kwargs: Additional parameters for EntityExtractor

    Returns:
        ExtractedEntities with all extracted information

    """
    extractor = EntityExtractor(**kwargs)
    return extractor.extract(text)
