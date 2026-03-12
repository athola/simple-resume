# ATS API Reference

**Version:** 0.3.2
**Last Updated:** 2026-03-11
**Stability:** Public API exports follow semantic versioning guarantees
**Parent:** [API Reference](API-Reference.md)

---

## ATS Scoring

Score resumes against job descriptions using multiple NLP algorithms in a tournament-style approach.

### `score_resume`

Convenience function to score a resume against a job description using the default tournament.

```python
from simple_resume import score_resume

result = score_resume(
    resume_text="Senior Python Developer with 5 years experience...",
    job_description="We are looking for a Senior Engineer..."
)

print(f"Match score: {result.overall_score * 100:.1f}%")
print(f"Algorithms used: {result.metadata['scorer_names']}")
```

**Parameters:**
- `resume_text: str` - Full resume text
- `job_description: str` - Full job description text
- `custom_scorers: list[BaseScorer] | None` - Optional custom scoring algorithms
- `percentage: bool` - If True (default), add `percentage_score` (0-100) to metadata

**Returns:** `TournamentResult`

### `ScoringMode`

Enum for selecting tournament weight presets. Different modes optimize for different evaluators.

```python
from simple_resume import ScoringMode

ScoringMode.ATS             # "ats" — optimized for automated tracking systems
ScoringMode.HUMAN_REVIEWER  # "human" — optimized for human recruiter evaluation
```

**Weight presets (with BERT):**

| Scorer | ATS | Human Reviewer |
|--------|-----|----------------|
| BERT | 0.35 | 0.45 |
| TF-IDF | 0.30 | 0.25 |
| Jaccard | 0.20 | 0.10 |
| Keyword | 0.15 | 0.20 |

Human reviewer mode also enables creative term expansion by default.

### `ATSTournament`

Multi-algorithm tournament runner for resume-job matching.

```python
from simple_resume import ATSTournament, ScoringMode, TFIDFScorer, JaccardScorer

# Default tournament (ATS mode)
tournament = ATSTournament()

# Human reviewer mode — emphasizes semantic similarity
tournament = ATSTournament(scoring_mode=ScoringMode.HUMAN_REVIEWER)

# Custom tournament with specific weights
tournament = ATSTournament(scorers=[
    TFIDFScorer(weight=0.5),
    JaccardScorer(weight=0.5),
])

result = tournament.score(resume_text, job_description)
```

**Parameters:**
- `scorers: list[BaseScorer] | None` - List of scoring algorithms (defaults to TF-IDF, Jaccard, Keyword)
- `include_bert: bool` - Whether to include BERT scorer if available (default: True)
- `bert_model_name: str | None` - Override BERT model name; shell layer can resolve from environment or config
- `scoring_mode: ScoringMode` - Weight preset to use (default: `ScoringMode.ATS`)

**Methods:**
- `score(resume_text, job_description, **kwargs) -> TournamentResult` - Score resume against job
- `get_top_matches(resumes, job_description, top_n=10) -> list` - Rank multiple resumes

### `TFIDFScorer`

TF-IDF + Cosine Similarity scorer for statistical keyword analysis.

```python
from simple_resume import TFIDFScorer

scorer = TFIDFScorer(
    weight=1.0,
    max_features=1000,
    ngram_range=(1, 2)  # Unigrams + bigrams
)
result = scorer.score(resume_text, job_description)
```

**Pros:** Fast, interpretable, good for exact keyword matching
**Cons:** Misses semantic meaning, no context understanding

### `JaccardScorer`

Jaccard similarity + N-gram overlap scorer for phrase matching.

```python
from simple_resume import JaccardScorer

scorer = JaccardScorer(
    weight=1.0,
    ngram_range=(1, 3),  # Unigrams to trigrams
    case_sensitive=False
)
result = scorer.score(resume_text, job_description)
```

**Pros:** Simple, interpretable, good for exact phrase matching
**Cons:** Limited to surface-level matching, misses semantic variations

### `KeywordScorer`

Exact keyword match scorer with fuzzy tolerance.

```python
from simple_resume import KeywordScorer
from simple_resume.core.ats.keyword import KeywordScorerConfig

scorer = KeywordScorer(
    weight=1.0,
    config=KeywordScorerConfig(
        fuzzy_threshold=0.85,
        extract_keywords=True,
    ),
)
result = scorer.score(resume_text, job_description)
```

**Pros:** Fast, simple, good for hard requirements
**Cons:** Misses semantic variations, vulnerable to keyword stuffing

### `BERTScorer` (Optional)

Semantic similarity scorer using sentence-transformers. Requires the `bert` extra.

```bash
# Install with bert extra
uv add simple-resume[bert]
pip install simple-resume[bert]
```

```python
from simple_resume import BERTScorer

# BERTScorer is None if sentence-transformers not installed
if BERTScorer is not None:
    scorer = BERTScorer(
        weight=1.0,
        model_name="all-MiniLM-L6-v2"  # Default model
    )
    result = scorer.score(resume_text, job_description)
```

**Pros:** Understands semantic meaning, handles synonyms and paraphrasing
**Cons:** Slower than statistical methods, requires GPU for best performance

### `ScorerName` and `ScorerSelection`

Enumerations for algorithm identification.

```python
from simple_resume import ScorerName, ScorerSelection

# Algorithm names (internal identifiers)
ScorerName.TFIDF_COSINE      # "tfidf_cosine"
ScorerName.JACCARD_NGRAM     # "jaccard_ngram"
ScorerName.KEYWORD_EXACT     # "keyword_exact"
ScorerName.BERT_SEMANTIC     # "bert_semantic"

# Selection shortcuts (user-facing)
ScorerSelection.TFIDF        # "tfidf"
ScorerSelection.JACCARD      # "jaccard"
ScorerSelection.KEYWORD      # "keyword"
ScorerSelection.BERT         # "bert"
```

### `BaseScorer`

Abstract base class for implementing custom scoring algorithms.

```python
from simple_resume import BaseScorer, ScorerResult

class CustomScorer(BaseScorer):
    def score(self, resume_text, job_description, **kwargs):
        # Your scoring logic here
        score = 0.75  # Example score
        return ScorerResult(
            name="custom",
            score=score,
            weight=self.weight,
            details={"custom_metric": 123}
        )
```

### `TournamentResult`

Result from running multiple scoring algorithms.

```python
from simple_resume import TournamentResult

result.overall_score  # Final weighted average (0-1)
result.algorithm_results  # List of individual ScorerResult
result.component_breakdown  # Scores by rubric component
result.metadata  # Tournament metadata
result.to_dict()  # Convert to dictionary
```

### `ScorerResult`

Result from an individual scoring algorithm.

```python
from simple_resume import ScorerResult

result.name  # Algorithm name
result.score  # Raw score (0-1)
result.weighted_score  # Score × weight
result.details  # Algorithm-specific details
result.component_scores  # Component breakdown
result.to_dict()  # Convert to dictionary
```

### `ExtractedEntities`

Structured entities extracted from resume or job description.

```python
from simple_resume import EntityExtractor

extractor = EntityExtractor(
    extract_keywords=True,
    custom_skills=["Golang", "Rust"]
)
entities = extractor.extract(text)

entities.skills  # List of skills
entities.experience_years  # Total years
entities.degrees  # List of degrees
entities.certifications  # List of certifications
entities.keywords  # TF-IDF keywords (word, score)
entities.to_dict()  # Convert to dictionary
```

### `ParsedDocument`

Lazy-evaluated parsed document for efficient entity extraction. Implements the parse-once architecture.

```python
from simple_resume import parse, ParsedDocument

# Create via parse() function (recommended)
doc = parse("  Resume text   here...  ")

# Lazy properties (computed once on first access)
doc.raw_text         # Original input
doc.normalized_text  # Whitespace-normalized
doc.lowercase_text   # Lowercase for case-insensitive matching
doc.lines            # Non-empty lines
doc.sentences        # Sentence-split text
doc.word_tokens      # Alphabetic tokens

# Section finding helper
skills_section = doc.find_section(r"Skills|Technologies")
```

**Properties:** Each property is computed once and cached via `@cached_property`.

### `Degree`

Structured representation of an educational degree.

```python
from simple_resume import Degree

degree = Degree(
    type="Bachelor",
    school="MIT",
    field="Computer Science"
)

degree.to_dict()  # {"type": "Bachelor", "school": "MIT", "field": "Computer Science"}
```

### `EntityExtractor`

Extract structured entities from unstructured text. Accepts both raw strings and `ParsedDocument` objects.

```python
from simple_resume import EntityExtractor, extract_entities, parse

# Class-based usage with string
extractor = EntityExtractor(extract_keywords=True)
entities = extractor.extract(resume_text)

# Class-based with ParsedDocument (efficient for multiple extractions)
doc = parse(resume_text)
entities = extractor.extract(doc)

# Function-based usage
entities = extract_entities(resume_text, custom_skills=["Kubernetes"])
```

### `ATSReportGenerator`

Generate human-readable reports from tournament results.

```python
from simple_resume import ATSReportGenerator
from pathlib import Path

report_gen = ATSReportGenerator(
    result=tournament_result,
    resume_file="my_resume.yaml",
    job_file="job_description.txt",
    job_url="https://company.com/jobs/123"
)

# Generate report content
yaml_report = report_gen.generate_yaml()
json_report = report_gen.generate_json(indent=2)

# Save to file (shell layer responsibility)
Path("output/ats_report.yaml").write_text(yaml_report)
```

**Output includes:**
- Overall score with status label
- Algorithm breakdown with individual scores
- Component scores (experience, skills, semantic, keywords)
- Recommendations for improvement
