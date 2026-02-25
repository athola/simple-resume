# Design: PYOK, LinkedIn Import, Job Post Tailoring

**Issues**: #8, #9, #10
**Date**: 2026-02-24
**Branch**: pyok-0.3.0
**Version target**: 0.3.0

## Summary

Add LLM-powered features to simple-resume: pass-your-own-key (PYOK) infrastructure,
LinkedIn profile import, and job posting resume tailoring. All LLM features are gated
behind the `[llm]` optional dependency.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM client | litellm unified client | Single interface to 100+ providers |
| LinkedIn input | URL scraping + file import | Maximum flexibility per issue #9 |
| Tailor output | New YAML + ATS report | Non-destructive, integrates with existing ATS |
| Feature gating | `requires_llm` decorator + optional deps | Clear install message when missing |

## Architecture

### Layer Separation (FCIS Pattern)

```text
Core (pure, no I/O, no API keys):
  core/llm/protocol.py      - LLMProvider ABC + result types
  core/llm/prompts.py        - Prompt templates as pure data
  core/importers/linkedin.py - LinkedIn data -> resume schema transform
  core/ats/tailor.py         - Job gap analysis, resume diff scoring

Shell (I/O, side effects, API calls):
  shell/llm/client.py        - litellm wrapper implementing LLMProvider
  shell/llm/config.py        - API key resolution (CLI args, env vars)
  shell/llm/gate.py          - requires_llm decorator, availability check
  shell/importers/linkedin_fetcher.py - URL scraping + file reading
  shell/cli/_tailor.py        - tailor subcommand
  shell/cli/_import.py        - import subcommand
```

### Feature Gating

```python
# shell/llm/gate.py
def is_llm_available() -> bool:
    """Check if litellm is installed."""
    try:
        import litellm  # noqa: F401

        return True
    except ImportError:
        return False


def requires_llm(func):
    """Decorator that gates functions behind [llm] dependency."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not is_llm_available():
            raise LLMNotAvailableError(
                "LLM features require: pip install simple-resume[llm]"
            )
        return func(*args, **kwargs)

    return wrapper
```

CLI commands that need LLM (`tailor`, LLM-assisted `import`) check availability
at dispatch time and show a clear install message.

### Dependencies

```toml
[project.optional-dependencies]
llm = ["litellm>=1.0,<2.0"]
linkedin = ["beautifulsoup4>=4.12,<5.0"]
all = ["simple-resume[llm,linkedin]"]
```

Note: `requests` is already a transitive dep of litellm. beautifulsoup4 is already
a dev dependency. LinkedIn file parsing (PDF) reuses existing PDF reading from ATS.

### New CLI Commands

```bash
# PYOK is a flag on LLM-powered commands, not a standalone command
# API key via --api-key or env var (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)

# Issue #9: Import from LinkedIn
simple-resume import --linkedin <url-or-file> [--api-key KEY] [--model MODEL]
# Without LLM: basic structured extraction from HTML/PDF
# With LLM: enhanced extraction with skill categorization

# Issue #10: Tailor resume for job posting
simple-resume tailor <resume> <job-posting> --api-key KEY --model MODEL
# job-posting: file path or URL
# Output: {resume}_tailored.yaml + generates PDF
# --report: ATS gap analysis report (yaml/json/text format)
# --report-only: just the report, no tailored resume
```

### Core Protocols

```python
# core/llm/protocol.py
class LLMProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, system: str = "", **kwargs) -> str: ...

    @abstractmethod
    def complete_structured(self, prompt: str, schema: dict, **kwargs) -> dict: ...


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.3
    max_tokens: int = 4096
```

### Prompt Strategy

All prompts stored in `core/llm/prompts.py` as template strings:

- `TAILOR_RESUME_PROMPT` - Rewrite resume bullets for job alignment
- `EXTRACT_JOB_REQUIREMENTS_PROMPT` - Parse job posting into structured data
- `LINKEDIN_ENHANCE_PROMPT` - Categorize/enhance LinkedIn extracted data
- `GENERATE_COLOR_SCHEME_PROMPT` - Suggest colors from company URL (issue #8)

### LinkedIn Import Flow

```text
URL/File -> fetch/read -> raw content
  -> detect format (HTML/PDF/CSV/text)
  -> extract structured data (BeautifulSoup for HTML, existing PDF reader, CSV parser)
  -> [optional: LLM enhance extracted data]
  -> map to simple-resume YAML schema
  -> write {name}.yaml
```

### Tailor Flow

```text
Resume YAML + Job Posting (file/URL)
  -> read both inputs
  -> extract job requirements (LLM-assisted)
  -> run ATS tournament (existing scorer)
  -> generate tailored resume (LLM rewrites bullets, adds keywords)
  -> validate tailored YAML (existing validation)
  -> write {name}_tailored.yaml
  -> [optional: generate PDF]
  -> [optional: --report generates gap analysis]
```

### Error Handling

New exceptions in `core/exceptions.py`:

- `LLMNotAvailableError(SimpleResumeError)` - missing [llm] dep
- `LLMError(SimpleResumeError)` - API call failures
- `ImportError_(SimpleResumeError)` - LinkedIn import failures
- `ScrapingError(SimpleResumeError)` - URL fetch failures

### Testing Strategy

- Core protocols: unit tests with mock LLM responses
- Prompt templates: snapshot tests for prompt structure
- LinkedIn parser: unit tests with fixture HTML/PDF/CSV files
- Tailor flow: integration tests with mocked litellm
- Feature gating: tests verify graceful degradation without [llm]
- CLI commands: integration tests with subprocess + mocked services

### Public API Additions to `__init__.py`

```python
# New exports (all gated behind availability checks)
LLMProvider, LLMConfig, LLMNotAvailableError, LLMError
import_linkedin, tailor_resume
```

## Implementation Phases

1. **Phase 1: PYOK Infrastructure** (#8) - protocol, client, gating, config
2. **Phase 2a: LinkedIn Import** (#9) - parser, fetcher, CLI command
3. **Phase 2b: Job Post Tailoring** (#10) - tailor flow, CLI command, report
4. **Phase 3: Integration** - public API, docs, version bump to 0.3.0
