# ATS Updates v0.3.2 Design Spec

Covers issues #62, #81, #82, #101, #102, #103, #104, #105.

Branch: `further-ats-updates-0.3.2`

## 1. Screen Fixes (#101, #102, #103)

### #101 — Latin-1 fallback warning

In `_read_file_text()` (`shell/cli/_screen.py`), emit `warnings.warn()` when
UTF-8 decoding fails and latin-1 fallback fires. Warning includes filename and
suggests checking file encoding.

Note: This uses Python's `warnings.warn()` mechanism, which is independent from
`_collect_ats_warnings()` (that pipeline inspects `TournamentResult` objects).
The warning fires at file-read time before scoring begins. Test via
`pytest.warns(UserWarning)`.

### #102 — Report write error handling

Wrap `_output_report()`'s `write_text()` call in `try/except OSError`. Print
error to stderr (not stdout) so automated pipelines can detect the failure.
Return exit code 0 since the screening result itself is valid — the scoring
completed successfully, only the file write failed.

### #103 — Code quality (S1, S2, S3)

- **S1**: Replace custom `Args` class in test files with
  `argparse.Namespace(**defaults)`.
- **S2**: `_handle_batch` currently has 5 params (under ruff's threshold).
  Adding `report_format` and `verbose` in #105 pushes it to 7. Group the new
  display-related params into the existing `_BatchDisplayOpts` dataclass instead
  of adding loose params, keeping the function signature clean.
- **S3**: Fix `_collect_resume_files` docstring from "Collect readable resume
  files" to "Collect resume files with supported suffixes".

## 2. Batch Format/Verbose (#105)

Pass `report_format` and `verbose` arguments through to `_handle_batch()` via
the existing `_BatchDisplayOpts` dataclass (add `report_format: str` and
`verbose: bool` fields).

**Key change in batch loop**: Store full `TournamentResult` objects per resume
instead of just `overall_score`. Change `results` from
`list[tuple[str, float]]` to `list[tuple[str, TournamentResult]]` so structured
reports have access to algorithm breakdowns.

- **JSON/YAML batch reports**: Build a top-level dict with metadata (job file,
  count, timestamp) and a `results` list. Each entry includes resume name,
  overall score, status label, and (for structured formats) full algorithm
  breakdown from `TournamentResult.algorithm_results`.
- **Verbose in batch mode**: For text format, add per-resume algorithm score
  columns to the table. For structured formats, include `algorithm_results`
  and `component_breakdown` in each entry.
- Backwards compatible: default text format behavior unchanged.
- `_format_batch_report()` signature changes to accept
  `list[tuple[str, TournamentResult]]` and gains `report_format` and `verbose`
  parameters.

## 3. PDF/HTML Text Extraction (#104)

### Dependencies

Add as core dependencies (lightweight — pdfplumber pulls only pdfminer.six and
pypdfium2, no heavy transitive deps like Pillow or cryptography):

- `pdfplumber>=0.11,<1.0`
- `beautifulsoup4>=4.12,<5.0` (move from `linkedin` optional extra to core)

The `linkedin` optional extra becomes empty after this move. Remove it and
update `all` extra to `simple-resume[llm]`.

### Architecture

Shell layer (`_screen.py`):

- `_extract_pdf_text(path: Path) -> str`: Uses `pdfplumber.open()`,
  concatenates `page.extract_text()` per page with newline separators.
- `_extract_html_text(path: Path) -> str`: Uses
  `BeautifulSoup(content, "html.parser").get_text(separator="\n")`.
- `_read_file_text()` dispatches to these based on suffix.

Update `_RESUME_SUFFIXES` to include `.pdf`, `.html`, `.htm`.
Remove these from `_UNSUPPORTED_SUFFIXES`.

### Error handling

- Missing `pdfplumber`: Should not happen (core dep), but import guard with
  clear error if somehow absent.
- Corrupt/empty PDF: Catch `pdfplumber` exceptions, raise `ValidationError`
  with descriptive message.
- Empty extraction result: Warn user, proceed with empty string (scorer will
  produce low scores naturally).

## 4. Taxonomy APIs — Hybrid (#81, #82)

### Offline bundles (default, no config needed)

- **O\*NET**: `src/simple_resume/core/ats/taxonomy_data/onet_skills.py`
  containing `ONET_SKILLS: list[str]` — curated ~500-1000 skills from O\*NET
  Technology Skills and Tools & Technology categories.
- **LinkedIn**: `src/simple_resume/core/ats/taxonomy_data/linkedin_skills.py`
  containing `LINKEDIN_SKILLS: list[str]` — curated comprehensive skills list.
- `__init__.py` in `taxonomy_data/` exports both lists.
- `SkillsTaxonomyFetcher` gains `_load_onet_bundle()` and
  `_load_linkedin_bundle()` methods returning these lists.

### Live API (opt-in)

Shell layer `src/simple_resume/shell/ats/taxonomy_fetcher.py`:

- `OnetApiFetcher`: Uses `urllib.request` with basic auth. Requires env vars
  `ONET_API_USERNAME` and `ONET_API_PASSWORD` (free registration at
  onetonline.org). REST endpoint for technology skills.
- `LinkedInApiFetcher`: Stub with clear extension point. LinkedIn's API
  requires OAuth app approval, so this documents the integration path without
  requiring credentials.
- Enabled via `TaxonomyConfig(enabled=True)` + env vars present.
- Responses cached via `TaxonomyCache` protocol with 7-day TTL.

### Merged skills pipeline

`get_enhanced_skills()` signature changes from
`(use_taxonomy: bool, taxonomy: str)` to
`(sources: list[TaxonomySource] | None = None, config: TaxonomyConfig | None = None)`.

When `sources` is None (default), all available sources are used:

1. Hardcoded skills (102, existing) — always included
2. O\*NET bundle — always included
3. LinkedIn bundle — always included
4. Live API results — only if `config.enabled=True` and env vars present

`SkillsTaxonomyFetcher.get_skills()` dispatch flow:

1. Start with `HARDCODED_SKILLS`
2. Call `_load_onet_bundle()` and `_load_linkedin_bundle()` (always succeed, no I/O)
3. If `config.enabled`, attempt `_fetch_onet()` and `_fetch_linkedin()` via shell-layer fetchers, falling back silently on error

Deduplicated and normalized to lowercase. Returns `list[str]`.

## 5. Creative Language & Human Reviewer Mode (#62)

### ScoringMode (core)

```python
class ScoringMode(str, Enum):
    ATS = "ats"
    HUMAN_REVIEWER = "human"


@dataclass
class ScoringModeConfig:
    mode: ScoringMode = ScoringMode.ATS
    weights: dict[str, float] | None = None  # Override preset weights
    enable_creative_expansion: bool | None = None  # None = mode default
```

### Weight presets

| Scorer | ATS | Human Reviewer |
|--------|-----|----------------|
| BERT   | 0.35 | 0.45 |
| TF-IDF | 0.30 | 0.25 |
| Jaccard| 0.20 | 0.10 |
| Keyword| 0.15 | 0.20 |

Without BERT:

| Scorer | ATS | Human Reviewer |
|--------|-----|----------------|
| TF-IDF | 0.40 | 0.35 |
| Jaccard| 0.30 | 0.15 |
| Keyword| 0.30 | 0.50 |

### Creative term expansion

- `ScoringMode.HUMAN_REVIEWER` sets `enable_creative_expansion = True`
  by default (overridable via `ScoringModeConfig`).
- `ScoringMode.ATS` keeps `enable_creative_expansion = False` (current
  behavior preserved).
- Existing `creative_terms.py` dictionaries handle all synonym mapping.

### CLI integration

New `--mode {ats,human}` flag on `sr screen`:

- Default: `ats` (backwards compatible)
- Applies to both single and batch modes
- Passed through `_build_tournament()` which configures weights accordingly

### Tournament integration

`ATSTournament.__init__()` gains an optional `scoring_mode: ScoringMode`
parameter (default: `ScoringMode.ATS`). When `scorers` is None (default path),
the mode determines which weight preset to use when constructing default
scorers. When `scorers` is explicitly provided, `scoring_mode` has no effect on
weights (the caller owns the scorer configuration).

`_build_tournament()` in `_screen.py` reads the `--mode` CLI arg and passes it
through. It also sets `KeywordScorerConfig(enable_creative_expansion=True)`
when mode is `HUMAN_REVIEWER` before constructing the `KeywordScorer`.

## Execution Order

1. **Batch A** (parallel): #101, #102, #103 — independent screen fixes
2. **Batch B**: #105 — batch format/verbose (same file area as A)
3. **Batch C**: #104 — PDF/HTML extraction (independent)
4. **Batch D** (parallel): #81, #82 — taxonomy bundles + API stubs
5. **Batch E**: #62 — scoring mode + creative language

Batches C and D can run in parallel with each other.

## Version Bump

Bump version to 0.3.2 in `pyproject.toml`, `src/simple_resume/__init__.py`,
and `uv.lock`. Add CHANGELOG.md entry. Done as final commit.

## Test Strategy

All changes follow TDD: failing test first, minimal implementation, refactor.

### Unit tests

- **#101**: Test that latin-1 file triggers warning via `pytest.warns()`
- **#102**: Test `OSError` on write produces correct stderr output, exit code 0
- **#103**: Verify `Namespace` works in existing tests, docstring assertion
- **#105**: Test batch with `--format json`, `--format yaml`, `--verbose`;
  verify `TournamentResult` data flows through to structured output
- **#104**: Test PDF/HTML extraction with fixture files, corrupt file handling
- **#81/#82**: Test bundle loading, merged pipeline deduplication, live API
  mocking
- **#62**: Test mode presets, weight overrides, creative expansion toggle,
  CLI flag parsing

### Integration tests

- PDF extraction -> scoring -> batch report: end-to-end with a small test PDF
- Taxonomy merge -> tournament scoring in human mode: verify expanded skills
  affect keyword matching results

## Files Changed (estimated)

| File | Issues |
|------|--------|
| `shell/cli/_screen.py` | #101, #102, #103, #104, #105 |
| `shell/cli/main.py` | #62, #105 |
| `core/ats/taxonomy.py` | #81, #82 |
| `core/ats/taxonomy_data/onet_skills.py` | #81 (new) |
| `core/ats/taxonomy_data/linkedin_skills.py` | #82 (new) |
| `core/ats/taxonomy_data/__init__.py` | #81, #82 (new) |
| `shell/ats/taxonomy_fetcher.py` | #81, #82 (new) |
| `core/ats/tournament.py` | #62 |
| `core/ats/constants.py` | #62 |
| `core/ats/keyword.py` | #62 |
| `pyproject.toml` | #104, version bump |
| `src/simple_resume/__init__.py` | version bump |
| `tests/unit/test_cli_ats.py` | #101, #102, #103, #105 |
| `tests/unit/test_cli_screen_batch.py` | #105 |
| `tests/unit/test_taxonomy.py` | #81, #82 (new or extend) |
| `tests/unit/test_scoring_mode.py` | #62 (new) |
| `tests/unit/test_pdf_html_extraction.py` | #104 (new) |
