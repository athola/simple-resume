# ATS Updates v0.3.2 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 8 ATS-related issues (#62, #81, #82, #101, #102, #103, #104, #105) adding screen fixes, PDF/HTML extraction, taxonomy API bundles, and human reviewer scoring mode.

**Architecture:** Functional core / imperative shell. Pure scoring logic lives in `src/simple_resume/core/ats/`, CLI orchestration in `src/simple_resume/shell/cli/_screen.py`. New taxonomy data bundles go in core, live API fetchers go in shell.

**Tech Stack:** Python 3.10+, pytest, pdfplumber, beautifulsoup4, urllib.request (stdlib)

**Spec:** `docs/superpowers/specs/2026-03-11-ats-updates-0.3.2-design.md`

**Branch:** `further-ats-updates-0.3.2`

---

## Chunk 1: Screen Fixes (#101, #102, #103)

### Task 1: Latin-1 fallback warning (#101)

**Files:**

- Modify: `src/simple_resume/shell/cli/_screen.py:1-6,200-205`
- Test: `tests/unit/test_cli_ats.py:598-611`

- [ ] **Step 1: Write failing test**

In `tests/unit/test_cli_ats.py`, add a test in `TestReadFileTextEncoding`:

```python
def test_latin1_fallback_emits_warning(self, tmp_path: Path, story: Scenario) -> None:
    story.given("a text file with latin-1 encoded characters")
    latin1_file = tmp_path / "resume.txt"
    latin1_file.write_bytes("Résumé with café".encode("latin-1"))

    story.when("reading the file")
    with pytest.warns(UserWarning, match="latin-1"):
        content = cli._read_file_text(latin1_file)

    story.then("a warning is emitted and the content is read")
    assert "caf" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_cli_ats.py::TestReadFileTextEncoding::test_latin1_fallback_emits_warning -v`
Expected: FAIL — no warning emitted

- [ ] **Step 3: Implement warning in `_read_file_text()`**

In `src/simple_resume/shell/cli/_screen.py`, add `import warnings` to the imports (line 2 area), then modify lines 203-205:

```text
except UnicodeDecodeError:
    # Try with different encoding
    warnings.warn(
        f"File '{file_path.name}' is not valid UTF-8, falling back to latin-1 encoding. "
        "Check the file encoding if text appears garbled.",
        UserWarning,
        stacklevel=2,
    )
    return file_path.read_text(encoding="latin-1")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_cli_ats.py::TestReadFileTextEncoding -v`
Expected: PASS (both existing and new test)

- [ ] **Step 5: Commit**

```bash
git add src/simple_resume/shell/cli/_screen.py tests/unit/test_cli_ats.py
git commit -m "fix: warn on silent latin-1 encoding fallback (#101)"
```

### Task 2: Report write error handling (#102)

**Files:**

- Modify: `src/simple_resume/shell/cli/_screen.py:61-68`
- Test: `tests/unit/test_cli_ats.py:330-356`

- [ ] **Step 1: Write failing test**

In `tests/unit/test_cli_ats.py`, add to `TestOutputReport`:

```python
def test_write_failure_prints_error_to_stderr(
    self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
) -> None:
    story.given("a read-only output path that will fail to write")
    read_only_dir = tmp_path / "readonly"
    read_only_dir.mkdir()
    read_only_dir.chmod(0o444)
    out_file = read_only_dir / "subdir" / "report.txt"

    story.when("outputting the report to a path that fails")
    _output_report("report text", out_file)

    story.then("error is printed to stderr, not stdout")
    captured = capsys.readouterr()
    assert "report text" not in captured.out
    assert "failed" in captured.err.lower() or "error" in captured.err.lower()
    read_only_dir.chmod(0o755)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_cli_ats.py::TestOutputReport::test_write_failure_prints_error_to_stderr -v`
Expected: FAIL — unhandled OSError

- [ ] **Step 3: Implement error handling in `_output_report()`**

In `src/simple_resume/shell/cli/_screen.py`, add `import sys` to imports, modify `_output_report()` (lines 61-68):

```python
def _output_report(content: str, output_path: Path | None) -> None:
    """Print or save a report."""
    if output_path:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            print(f"Report saved to: {output_path}")
        except OSError as exc:
            print(
                f"Screening completed but report could not be saved to "
                f"'{output_path}': {exc}",
                file=sys.stderr,
            )
    else:
        print(content)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_cli_ats.py::TestOutputReport -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add src/simple_resume/shell/cli/_screen.py tests/unit/test_cli_ats.py
git commit -m "fix: handle report file write errors gracefully (#102)"
```

### Task 3: Code quality improvements (#103)

**Files:**

- Modify: `tests/unit/test_cli_screen_batch.py:20-40`
- Modify: `src/simple_resume/shell/cli/_screen.py:52-53`

- [ ] **Step 1: Replace custom `Args` class with `argparse.Namespace` in batch tests**

In `tests/unit/test_cli_screen_batch.py`, replace `_make_args` (lines 20-40):

```python
import argparse


def _make_args(**kwargs):  # type: ignore[no-untyped-def]
    """Build a minimal argparse.Namespace for screen commands."""
    defaults = {
        "resume": None,
        "job": None,
        "output": None,
        "format": "text",
        "scorers": "all",
        "verbose": False,
        "batch": False,
        "top": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)
```

- [ ] **Step 2: Fix `_collect_resume_files` docstring**

In `src/simple_resume/shell/cli/_screen.py` line 53, change:

```python
"""Collect readable resume files from a directory."""
```

to:

```python
"""Collect resume files with supported suffixes from a directory."""
```

- [ ] **Step 3: Run existing tests to verify no regressions**

Run: `uv run pytest tests/unit/test_cli_screen_batch.py tests/unit/test_cli_ats.py -v`
Expected: PASS (all existing tests)

- [ ] **Step 4: Commit**

```bash
git add tests/unit/test_cli_screen_batch.py src/simple_resume/shell/cli/_screen.py
git commit -m "refactor: code quality improvements from PR #100 review (#103)"
```

## Chunk 2: Batch Format/Verbose (#105)

### Task 4: Add format/verbose fields to `_BatchDisplayOpts`

**Files:**

- Modify: `src/simple_resume/shell/cli/_screen.py:33-38,71-100`

- [ ] **Step 1: Extend `_BatchDisplayOpts` dataclass**

In `src/simple_resume/shell/cli/_screen.py`, modify the dataclass (lines 33-38):

```python
@dataclass(frozen=True)
class _BatchDisplayOpts:
    """Display and output options for batch screening."""

    top_n: int | None = None
    output_path: Path | None = None
    report_format: str = "text"
    verbose: bool = False
```

- [ ] **Step 2: Update `handle_screen_command` to pass format/verbose**

In `handle_screen_command()` (line 93), update the `_BatchDisplayOpts` creation:

```python
display = _BatchDisplayOpts(
    top_n=top_n,
    output_path=output_path,
    report_format=report_format,
    verbose=verbose,
)
```

- [ ] **Step 3: Run existing tests**

Run: `uv run pytest tests/unit/test_cli_screen_batch.py tests/unit/test_cli_ats.py -v`
Expected: PASS (no behavior change yet)

### Task 5: Store full `TournamentResult` in batch loop

**Files:**

- Modify: `src/simple_resume/shell/cli/_screen.py:133-177`

- [ ] **Step 1: Write failing test for structured batch output**

In `tests/unit/test_cli_screen_batch.py`, add:

```python
import json


class TestBatchFormatVerbose:
    """Batch mode respects --format and --verbose flags (#105)."""

    def test_batch_json_format(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("a directory with resumes and --format json")
        resumes_dir = tmp_path / "resumes"
        resumes_dir.mkdir()
        (resumes_dir / "resume_a.txt").write_text("Python developer with Django.")
        (resumes_dir / "resume_b.txt").write_text("Java developer with Spring.")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Looking for a Python developer.")

        story.when("running batch screen with json format")
        args = _make_args(resume=resumes_dir, job=job_file, batch=True, format="json")
        exit_code = handle_screen_command(args)

        story.then("valid JSON is produced with results array")
        output = capsys.readouterr().out
        assert exit_code == 0
        data = json.loads(output)
        assert "results" in data
        assert len(data["results"]) == 2

    def test_batch_yaml_format(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("a directory with resumes and --format yaml")
        resumes_dir = tmp_path / "resumes"
        resumes_dir.mkdir()
        (resumes_dir / "resume_a.txt").write_text("Python developer with Django.")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Looking for a Python developer.")

        story.when("running batch screen with yaml format")
        args = _make_args(resume=resumes_dir, job=job_file, batch=True, format="yaml")
        exit_code = handle_screen_command(args)

        story.then("YAML output is produced without text report header")
        output = capsys.readouterr().out
        assert exit_code == 0
        assert "BATCH ATS SCREENING REPORT" not in output
        assert "results:" in output or "overall_score" in output

    def test_batch_verbose_text_shows_algorithm_breakdown(
        self, tmp_path: Path, story: Scenario, capsys: pytest.CaptureFixture[str]
    ) -> None:
        story.given("a directory with resumes and --verbose flag")
        resumes_dir = tmp_path / "resumes"
        resumes_dir.mkdir()
        (resumes_dir / "resume_a.txt").write_text("Python developer with 5 years.")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Senior Python developer needed.")

        story.when("running batch screen with verbose")
        args = _make_args(resume=resumes_dir, job=job_file, batch=True, verbose=True)
        exit_code = handle_screen_command(args)

        story.then("algorithm details are shown in the report")
        output = capsys.readouterr().out
        assert exit_code == 0
        # Verbose batch should show scorer names
        assert "tfidf" in output.lower() or "keyword" in output.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_cli_screen_batch.py::TestBatchFormatVerbose -v`
Expected: FAIL — batch doesn't support format/verbose yet

- [ ] **Step 3: Implement batch loop changes**

In `_handle_batch()`, change `results` type to store full `TournamentResult`, and update `_format_batch_report()`:

Modify `_handle_batch()` (lines 133-177):

```python
def _handle_batch(
    resume_path: Path,
    job_path: Path,
    job_text: str,
    tournament: ATSTournament,
    display: _BatchDisplayOpts,
) -> int:
    """Screen all resumes in a directory against a job description."""
    if not resume_path.exists() or not resume_path.is_dir():
        print(f"Error: '{resume_path}' is not a directory.")
        return 1

    resume_files = _collect_resume_files(resume_path)
    if not resume_files:
        print(
            f"Error: No resume files found in '{resume_path}'. "
            f"Supported: {', '.join(sorted(_RESUME_SUFFIXES))}"
        )
        return 1

    # Score each resume, storing full TournamentResult
    results: list[tuple[str, TournamentResult]] = []
    for rfile in resume_files:
        try:
            text = _read_file_text(rfile)
        except (OSError, SimpleResumeError) as exc:
            print(f"  Skipping {rfile.name}: {exc}")
            continue
        if not text.strip():
            print(f"  Skipping {rfile.name}: file is empty")
            continue
        try:
            result = tournament.score(text, job_text)
        except Exception as exc:  # noqa: BLE001
            print(f"  Skipping {rfile.name}: scoring failed ({exc})")
            continue
        results.append((rfile.name, result))

    if not results:
        print("Error: No resumes could be scored successfully.")
        return 1

    report = _format_batch_report(
        results,
        str(job_path),
        top_n=display.top_n,
        report_format=display.report_format,
        verbose=display.verbose,
    )
    _output_report(report, display.output_path)
    return 0
```

- [ ] **Step 4: Implement `_format_batch_report()` with format/verbose support**

Replace `_format_batch_report()` (lines 326-364). Add `import json` and `import oyaml as yaml` to imports, and `from datetime import datetime, timezone`:

```python
def _format_batch_report(
    results: list[tuple[str, TournamentResult]],
    job_file: str,
    *,
    top_n: int | None = None,
    report_format: str = "text",
    verbose: bool = False,
) -> str:
    """Format batch screening results as a ranked report."""
    ranked = sorted(results, key=lambda x: x[1].overall_score, reverse=True)
    total = len(ranked)
    if top_n is not None and top_n > 0:
        ranked = ranked[:top_n]

    if report_format in ("json", "yaml"):
        return _format_batch_structured(ranked, job_file, total, report_format, verbose)

    return _format_batch_text(ranked, job_file, total, top_n, verbose)


def _format_batch_text(
    ranked: list[tuple[str, TournamentResult]],
    job_file: str,
    total: int,
    top_n: int | None,
    verbose: bool,
) -> str:
    """Format batch results as human-readable text."""
    lines = [
        "=" * 60,
        "BATCH ATS SCREENING REPORT",
        "=" * 60,
        "",
        f"Job description: {job_file}",
        f"Resumes scored:  {total}",
    ]
    if top_n is not None and top_n > 0 and top_n < total:
        lines.append(f"Showing top:     {len(ranked)}")
    lines.extend(
        [
            "",
            "-" * 60,
            "RANKED RESULTS",
            "-" * 60,
            "",
        ]
    )

    for rank, (name, result) in enumerate(ranked, 1):
        score_100 = result.overall_score * 100
        status = _get_status_label(score_100)
        lines.append(f"{rank}. {name:40s} {score_100:5.1f}/100  {status}")
        if verbose:
            for alg in result.algorithm_results:
                lines.append(
                    f"     {alg.name:36s} {alg.score * 100:5.1f}  "
                    f"(weight: {alg.weight})"
                )

    lines.extend(["", "=" * 60])
    return "\n".join(lines)


def _format_batch_structured(
    ranked: list[tuple[str, TournamentResult]],
    job_file: str,
    total: int,
    report_format: str,
    verbose: bool,
) -> str:
    """Format batch results as JSON or YAML."""
    entries = []
    for name, result in ranked:
        entry: dict[str, object] = {
            "resume": name,
            "overall_score": round(result.overall_score * 100, 1),
            "status": _get_status_label(result.overall_score * 100),
        }
        if verbose:
            entry["algorithm_results"] = [
                {
                    "name": alg.name,
                    "score": round(alg.score * 100, 1),
                    "weight": alg.weight,
                }
                for alg in result.algorithm_results
            ]
            entry["component_breakdown"] = {
                k: round(v, 4) for k, v in result.component_breakdown.items()
            }
        entries.append(entry)

    data: dict[str, object] = {
        "job_description": job_file,
        "resumes_scored": total,
        "results": entries,
    }

    if report_format == "json":
        return json.dumps(data, indent=2)
    return yaml.dump(data, default_flow_style=False, allow_unicode=True)
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/unit/test_cli_screen_batch.py -v`
Expected: PASS (all tests including new format/verbose tests)

- [ ] **Step 6: Run full test suite for regression check**

Run: `uv run pytest tests/unit/test_cli_ats.py tests/unit/test_cli_screen_batch.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/simple_resume/shell/cli/_screen.py tests/unit/test_cli_screen_batch.py
git commit -m "feat: batch mode respects --format and --verbose flags (#105)"
```

## Chunk 3: PDF/HTML Text Extraction (#104)

### Task 6: Add core dependencies

**Files:**

- Modify: `pyproject.toml:45-78`

- [ ] **Step 1: Add pdfplumber and beautifulsoup4 as core deps**

In `pyproject.toml`, add to `dependencies` (after `scikit-learn` line 52):

```toml
    "pdfplumber>=0.11,<1.0",
    "beautifulsoup4>=4.12,<5.0",
```

Remove `linkedin` optional extra (lines 73-75) and update `all` (lines 76-78):

```toml
all = [
    "simple-resume[llm]",
]
```

- [ ] **Step 2: Install new dependencies**

Run: `uv sync --quiet`

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add pdfplumber and beautifulsoup4 as core dependencies (#104)"
```

### Task 7: Implement PDF/HTML extraction

**Files:**

- Modify: `src/simple_resume/shell/cli/_screen.py:1-31,180-205`
- Create: `tests/unit/test_pdf_html_extraction.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_pdf_html_extraction.py`:

```python
"""Tests for PDF and HTML text extraction in ATS screening (#104)."""

from __future__ import annotations

from pathlib import Path

import pytest

from simple_resume.core.exceptions import ValidationError
from simple_resume.shell.cli import main as cli
from tests.bdd import Scenario


class TestPdfExtraction:
    """PDF text extraction via pdfplumber."""

    def test_extract_pdf_text(self, tmp_path: Path, story: Scenario) -> None:
        story.given("a simple PDF file created with pdfplumber")
        # Create a minimal PDF using reportlab-like content
        # We'll use pdfplumber's test helper or create a real PDF
        import pdfplumber
        from pdfplumber.utils.text import DEFAULT_X_DENSITY

        # Create PDF with fpdf2 if available, otherwise skip
        pytest.importorskip("pdfplumber")

        # Use a pre-built tiny PDF for testing
        pdf_path = tmp_path / "resume.pdf"
        _create_test_pdf(pdf_path, "Python developer with Django experience")

        story.when("reading the PDF file")
        content = cli._read_file_text(pdf_path)

        story.then("text is extracted from the PDF")
        assert "Python" in content

    def test_corrupt_pdf_raises_validation_error(
        self, tmp_path: Path, story: Scenario
    ) -> None:
        story.given("a corrupt PDF file")
        bad_pdf = tmp_path / "corrupt.pdf"
        bad_pdf.write_bytes(b"not a real pdf")

        story.when("reading the corrupt PDF")
        with pytest.raises(ValidationError, match="extract text"):
            cli._read_file_text(bad_pdf)

        story.then("a ValidationError is raised")


class TestHtmlExtraction:
    """HTML text extraction via BeautifulSoup."""

    def test_extract_html_text(self, tmp_path: Path, story: Scenario) -> None:
        story.given("an HTML file with resume content")
        html_file = tmp_path / "resume.html"
        html_file.write_text(
            "<html><body><h1>Jane Doe</h1>"
            "<p>Python developer with 5 years of experience.</p>"
            "</body></html>"
        )

        story.when("reading the HTML file")
        content = cli._read_file_text(html_file)

        story.then("text is extracted without HTML tags")
        assert "Jane Doe" in content
        assert "Python developer" in content
        assert "<html>" not in content

    def test_extract_htm_text(self, tmp_path: Path, story: Scenario) -> None:
        story.given("an .htm file")
        htm_file = tmp_path / "resume.htm"
        htm_file.write_text("<html><body><p>Go engineer</p></body></html>")

        story.when("reading the .htm file")
        content = cli._read_file_text(htm_file)

        story.then("text is extracted")
        assert "Go engineer" in content


class TestCollectResumeFilesWithNewFormats:
    """_collect_resume_files now includes PDF and HTML."""

    def test_collects_pdf_and_html(self, tmp_path: Path, story: Scenario) -> None:
        story.given("a directory with pdf, html, htm, and txt files")
        (tmp_path / "a.pdf").write_bytes(b"pdf")
        (tmp_path / "b.html").write_text("html")
        (tmp_path / "c.htm").write_text("htm")
        (tmp_path / "d.txt").write_text("txt")
        (tmp_path / "e.py").write_text("py")

        story.when("collecting resume files")
        from simple_resume.shell.cli._screen import _collect_resume_files

        files = _collect_resume_files(tmp_path)

        story.then("pdf, html, htm, and txt are included; py is excluded")
        names = [f.name for f in files]
        assert "a.pdf" in names
        assert "b.html" in names
        assert "c.htm" in names
        assert "d.txt" in names
        assert "e.py" not in names


def _create_test_pdf(path: Path, text: str) -> None:
    """Create a minimal PDF with the given text using fpdf2."""
    fpdf2 = pytest.importorskip("fpdf")
    pdf = fpdf2.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text=text)
    pdf.output(str(path))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_pdf_html_extraction.py -v`
Expected: FAIL — `_read_file_text` raises ValidationError for PDF/HTML

- [ ] **Step 3: Implement extraction functions**

In `src/simple_resume/shell/cli/_screen.py`:

Update `_RESUME_SUFFIXES` and `_UNSUPPORTED_SUFFIXES` (lines 29-30):

```python
_RESUME_SUFFIXES = {".txt", ".md", ".yaml", ".yml", ".json", ".pdf", ".html", ".htm"}
_UNSUPPORTED_SUFFIXES: set[str] = set()  # All formats now supported
```

Add extraction functions before `_read_file_text()`:

```python
def _extract_pdf_text(file_path: Path) -> str:
    """Extract text from a PDF file using pdfplumber."""
    import pdfplumber

    try:
        with pdfplumber.open(file_path) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n".join(pages)
    except Exception as exc:
        raise ValidationError(
            f"Could not extract text from PDF '{file_path.name}'",
            errors=[str(exc)],
            context={"file_path": str(file_path)},
            filename=str(file_path),
        ) from exc


def _extract_html_text(file_path: Path) -> str:
    """Extract text from an HTML file using BeautifulSoup."""
    from bs4 import BeautifulSoup

    raw = file_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "html.parser")
    return soup.get_text(separator="\n")
```

Update `_read_file_text()` to dispatch:

```python
def _read_file_text(file_path: Path) -> str:
    """Read text content from a file, handling various formats."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf_text(file_path)

    if suffix in {".html", ".htm"}:
        return _extract_html_text(file_path)

    # Read text content
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        warnings.warn(
            f"File '{file_path.name}' is not valid UTF-8, falling back to latin-1 encoding. "
            "Check the file encoding if text appears garbled.",
            UserWarning,
            stacklevel=2,
        )
        return file_path.read_text(encoding="latin-1")
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_pdf_html_extraction.py -v`
Expected: PASS

- [ ] **Step 5: Run full suite for regressions**

Run: `uv run pytest tests/unit/test_cli_ats.py tests/unit/test_cli_screen_batch.py tests/unit/test_pdf_html_extraction.py -v`
Expected: PASS — previous PDF/HTML `ValidationError` tests need updating since behavior changed

- [ ] **Step 6: Update old tests that expect `ValidationError` for PDF/HTML**

In `tests/unit/test_cli_ats.py`, update tests at lines 45-97. These three tests (`test_read_file_text_pdf_raises_validation_error`, `test_read_file_text_html_raises_validation_error`, `test_read_file_text_htm_raises_validation_error`) now expect extraction rather than errors. Replace them:

```python
def test_read_file_text_pdf_extracts_text(tmp_path: Path, story: Scenario) -> None:
    """Test that PDF files are read via pdfplumber extraction."""
    fpdf2 = pytest.importorskip("fpdf")
    story.given("a PDF file with text content")
    pdf_file = tmp_path / "resume.pdf"
    pdf = fpdf2.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text="Python developer")
    pdf.output(str(pdf_file))

    story.when("reading the PDF")
    content = cli._read_file_text(pdf_file)

    story.then("text is extracted from the PDF")
    assert "Python" in content


def test_read_file_text_html_extracts_text(tmp_path: Path, story: Scenario) -> None:
    """Test that HTML files are read via BeautifulSoup extraction."""
    story.given("an HTML file with resume content")
    html_file = tmp_path / "job.html"
    html_file.write_text("<html><body><p>Job posting content</p></body></html>")

    story.when("reading the HTML file")
    content = cli._read_file_text(html_file)

    story.then("text is extracted without tags")
    assert "Job posting content" in content
    assert "<html>" not in content


def test_read_file_text_htm_extracts_text(tmp_path: Path, story: Scenario) -> None:
    """Test that .htm files are also extracted."""
    story.given("a .htm file")
    htm_file = tmp_path / "job.htm"
    htm_file.write_text("<html><body>Job posting</body></html>")

    story.when("reading the .htm file")
    content = cli._read_file_text(htm_file)

    story.then("text is extracted")
    assert "Job posting" in content
```

- [ ] **Step 7: Run full test suite**

Run: `uv run pytest tests/unit/test_cli_ats.py tests/unit/test_pdf_html_extraction.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/simple_resume/shell/cli/_screen.py tests/unit/test_pdf_html_extraction.py tests/unit/test_cli_ats.py
git commit -m "feat: add PDF/HTML text extraction for ATS screening (#104)"
```

## Chunk 4: Taxonomy Bundles & APIs (#81, #82)

### Task 8: Create O\*NET skills bundle

**Files:**

- Create: `src/simple_resume/core/ats/taxonomy_data/__init__.py`
- Create: `src/simple_resume/core/ats/taxonomy_data/onet_skills.py`

- [ ] **Step 1: Write failing test**

Create or extend `tests/unit/test_taxonomy.py` (or add to existing file):

```python
"""Tests for taxonomy data bundles and enhanced skills pipeline (#81, #82)."""

from __future__ import annotations

import pytest

from tests.bdd import Scenario


class TestOnetBundle:
    """O*NET skills bundle loads correctly."""

    def test_onet_skills_is_nonempty_list(self, story: Scenario) -> None:
        story.given("the O*NET skills bundle module")
        from simple_resume.core.ats.taxonomy_data.onet_skills import ONET_SKILLS

        story.when("accessing the skills list")
        story.then("it contains a substantial number of skills")
        assert isinstance(ONET_SKILLS, (list, tuple))
        assert len(ONET_SKILLS) >= 200

    def test_onet_skills_contains_common_tech(self, story: Scenario) -> None:
        story.given("the O*NET skills bundle")
        from simple_resume.core.ats.taxonomy_data.onet_skills import ONET_SKILLS

        story.when("checking for common technology skills")
        skills_lower = {s.lower() for s in ONET_SKILLS}

        story.then("common skills are present")
        assert "python" in skills_lower
        assert "sql" in skills_lower
        assert "project management" in skills_lower
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_taxonomy.py::TestOnetBundle -v`
Expected: FAIL — module does not exist

- [ ] **Step 3: Create taxonomy_data package and O\*NET bundle**

Create `src/simple_resume/core/ats/taxonomy_data/__init__.py`:

```python
"""Bundled skills taxonomy data from O*NET and LinkedIn."""

from simple_resume.core.ats.taxonomy_data.linkedin_skills import LINKEDIN_SKILLS
from simple_resume.core.ats.taxonomy_data.onet_skills import ONET_SKILLS

__all__ = ["ONET_SKILLS", "LINKEDIN_SKILLS"]
```

Create `src/simple_resume/core/ats/taxonomy_data/onet_skills.py` with a curated list of ~500 skills from O\*NET Technology Skills and Tools categories. The subagent implementing this task should research and curate realistic O\*NET skills covering: programming languages, databases, frameworks, cloud platforms, DevOps tools, data science, project management, business tools, and industry-specific technologies.

The list should be a `tuple[str, ...]` constant named `ONET_SKILLS` with at least 400 entries.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_taxonomy.py::TestOnetBundle -v`
Expected: PASS

### Task 9: Create LinkedIn skills bundle

**Files:**

- Create: `src/simple_resume/core/ats/taxonomy_data/linkedin_skills.py`

- [ ] **Step 1: Write failing test**

Add to `tests/unit/test_taxonomy.py`:

```python
class TestLinkedInBundle:
    """LinkedIn skills bundle loads correctly."""

    def test_linkedin_skills_is_nonempty_list(self, story: Scenario) -> None:
        story.given("the LinkedIn skills bundle module")
        from simple_resume.core.ats.taxonomy_data.linkedin_skills import LINKEDIN_SKILLS

        story.when("accessing the skills list")
        story.then("it contains a substantial number of skills")
        assert isinstance(LINKEDIN_SKILLS, (list, tuple))
        assert len(LINKEDIN_SKILLS) >= 200

    def test_linkedin_skills_contains_soft_skills(self, story: Scenario) -> None:
        story.given("the LinkedIn skills bundle")
        from simple_resume.core.ats.taxonomy_data.linkedin_skills import LINKEDIN_SKILLS

        story.when("checking for soft skills common on LinkedIn")
        skills_lower = {s.lower() for s in LINKEDIN_SKILLS}

        story.then("professional soft skills are present")
        assert "leadership" in skills_lower
        assert "communication" in skills_lower
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_taxonomy.py::TestLinkedInBundle -v`
Expected: FAIL

- [ ] **Step 3: Create LinkedIn skills bundle**

Create `src/simple_resume/core/ats/taxonomy_data/linkedin_skills.py` with `LINKEDIN_SKILLS: tuple[str, ...]` — a curated list of skills commonly found on LinkedIn profiles. Should include both technical and soft skills, covering: leadership, communication, project management, industry skills, marketing, finance, design, engineering, etc. At least 400 entries.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_taxonomy.py::TestLinkedInBundle -v`
Expected: PASS

- [ ] **Step 5: Commit both bundles**

```bash
git add src/simple_resume/core/ats/taxonomy_data/
git commit -m "feat: add O*NET and LinkedIn skills data bundles (#81, #82)"
```

### Task 10: Update taxonomy fetcher to use bundles

**Files:**

- Modify: `src/simple_resume/core/ats/taxonomy.py:181-305`
- Test: `tests/unit/test_taxonomy.py`

- [ ] **Step 1: Write failing test for merged pipeline**

Add to `tests/unit/test_taxonomy.py`:

```python
from simple_resume.core.ats.taxonomy import (
    HARDCODED_SKILLS,
    SkillsTaxonomyFetcher,
    TaxonomyConfig,
    get_enhanced_skills,
)


class TestMergedSkillsPipeline:
    """get_enhanced_skills merges hardcoded + bundle skills."""

    def test_enhanced_skills_includes_hardcoded(self, story: Scenario) -> None:
        story.given("default taxonomy configuration")
        story.when("getting enhanced skills")
        skills = get_enhanced_skills()
        skills_lower = {s.lower() for s in skills}

        story.then("hardcoded skills are included")
        for skill in HARDCODED_SKILLS[:5]:
            assert skill.lower() in skills_lower

    def test_enhanced_skills_includes_bundles(self, story: Scenario) -> None:
        story.given("default taxonomy configuration")
        story.when("getting enhanced skills")
        skills = get_enhanced_skills()

        story.then("result is larger than hardcoded list alone")
        assert len(skills) > len(HARDCODED_SKILLS)

    def test_enhanced_skills_deduplicates(self, story: Scenario) -> None:
        story.given("skills from multiple sources with overlaps")
        story.when("getting enhanced skills")
        skills = get_enhanced_skills()
        skills_lower = [s.lower() for s in skills]

        story.then("no duplicates exist (case-insensitive)")
        assert len(skills_lower) == len(set(skills_lower))

    def test_fetcher_get_skills_without_api(self, story: Scenario) -> None:
        story.given("a fetcher with API disabled (default)")
        fetcher = SkillsTaxonomyFetcher()

        story.when("getting skills")
        skills = fetcher.get_skills()

        story.then("returns merged hardcoded + bundle skills")
        assert len(skills) > len(HARDCODED_SKILLS)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_taxonomy.py::TestMergedSkillsPipeline -v`
Expected: FAIL — current `get_enhanced_skills()` only returns hardcoded

- [ ] **Step 3: Implement merged pipeline**

In `src/simple_resume/core/ats/taxonomy.py`, update `SkillsTaxonomyFetcher` and `get_enhanced_skills()`:

Add import at top:

```python
from simple_resume.core.ats.taxonomy_data import LINKEDIN_SKILLS, ONET_SKILLS
```

Add bundle loader methods to `SkillsTaxonomyFetcher`:

```python
@staticmethod
def _load_onet_bundle() -> list[str]:
    """Load curated O*NET skills bundle (no I/O, always succeeds)."""
    return list(ONET_SKILLS)


@staticmethod
def _load_linkedin_bundle() -> list[str]:
    """Load curated LinkedIn skills bundle (no I/O, always succeeds)."""
    return list(LINKEDIN_SKILLS)
```

Update `get_skills()` to merge all sources:

```python
def get_skills(self, taxonomy: str | TaxonomySource = TaxonomySource.ONET) -> list[str]:
    """Get merged skills from hardcoded list, bundles, and optional API.

    Returns deduplicated, lowercase-normalized list of skills from:
    1. Hardcoded skills (always included)
    2. O*NET bundle (always included)
    3. LinkedIn bundle (always included)
    4. Live API results (only if config.enabled and API available)
    """
    all_skills: list[str] = list(HARDCODED_SKILLS)
    all_skills.extend(self._load_onet_bundle())
    all_skills.extend(self._load_linkedin_bundle())

    # Optionally fetch from live API
    if self._config.enabled:
        cached_skills = self._cache.get(taxonomy)
        if cached_skills is not None:
            logger.debug("Using cached skills from %s", taxonomy)
            all_skills.extend(cached_skills)
        else:
            try:
                api_skills = self._fetch_from_api(taxonomy)
                if api_skills:
                    self._cache.set(taxonomy, api_skills)
                    all_skills.extend(api_skills)
            except (
                OSError,
                ConnectionError,
                TimeoutError,
                ValueError,
                NotImplementedError,
            ) as exc:
                logger.warning("Failed to fetch from %s API: %s", taxonomy, exc)

    # Deduplicate (case-insensitive) preserving first occurrence
    seen: set[str] = set()
    unique: list[str] = []
    for skill in all_skills:
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            unique.append(skill)
    return unique
```

Update `get_enhanced_skills()`:

```python
def get_enhanced_skills(
    use_taxonomy: bool = False,
    taxonomy: str | TaxonomySource = TaxonomySource.ONET,
) -> list[str]:
    """Get skills with bundled taxonomy data and optional API integration.

    Always merges hardcoded + O*NET + LinkedIn bundles. When use_taxonomy=True,
    also attempts live API fetch with caching.
    """
    config = TaxonomyConfig(enabled=use_taxonomy)
    fetcher = SkillsTaxonomyFetcher(config)
    return fetcher.get_skills(taxonomy)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_taxonomy.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/simple_resume/core/ats/taxonomy.py tests/unit/test_taxonomy.py
git commit -m "feat: merge O*NET and LinkedIn bundles into skills pipeline (#81, #82)"
```

### Task 11: Create shell-layer API fetchers (stubs)

**Files:**

- Create: `src/simple_resume/shell/ats/__init__.py`
- Create: `src/simple_resume/shell/ats/taxonomy_fetcher.py`

- [ ] **Step 1: Write test for API fetcher stubs**

Add to `tests/unit/test_taxonomy.py`:

```python
class TestApiFetcherStubs:
    """Shell-layer API fetcher stubs are importable."""

    def test_onet_fetcher_exists(self, story: Scenario) -> None:
        story.given("the shell-layer taxonomy fetcher module")
        from simple_resume.shell.ats.taxonomy_fetcher import OnetApiFetcher

        story.when("instantiating the O*NET fetcher")
        fetcher = OnetApiFetcher()

        story.then("it has a fetch method")
        assert hasattr(fetcher, "fetch")

    def test_linkedin_fetcher_exists(self, story: Scenario) -> None:
        story.given("the shell-layer taxonomy fetcher module")
        from simple_resume.shell.ats.taxonomy_fetcher import LinkedInApiFetcher

        story.when("instantiating the LinkedIn fetcher")
        fetcher = LinkedInApiFetcher()

        story.then("it has a fetch method")
        assert hasattr(fetcher, "fetch")

    def test_onet_fetcher_requires_credentials(self, story: Scenario) -> None:
        story.given("an O*NET fetcher without credentials")
        from simple_resume.shell.ats.taxonomy_fetcher import OnetApiFetcher

        fetcher = OnetApiFetcher()

        story.when("attempting to fetch without env vars")
        with pytest.raises(NotImplementedError):
            fetcher.fetch()

        story.then("NotImplementedError is raised with guidance")
```

- [ ] **Step 2: Create shell/ats package and fetcher stubs**

Create `src/simple_resume/shell/ats/__init__.py`:

```python
"""Shell-layer ATS components with I/O and external API access."""
```

Create `src/simple_resume/shell/ats/taxonomy_fetcher.py`:

```python
"""Live taxonomy API fetchers (shell layer).

These fetchers handle network I/O for taxonomy APIs. They are opt-in
and require environment variables for authentication.

O*NET: Free registration at https://services.onetcenter.org/
LinkedIn: Requires OAuth app approval (stub only for now).
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


class OnetApiFetcher:
    """Fetch skills from O*NET Web Services API.

    Requires ONET_API_USERNAME and ONET_API_PASSWORD environment variables.
    Register for free at https://services.onetcenter.org/
    """

    def fetch(self) -> list[str]:
        """Fetch technology skills from O*NET API.

        Raises:
            NotImplementedError: Until live API integration is implemented.
                Set ONET_API_USERNAME and ONET_API_PASSWORD env vars.
        """
        username = os.environ.get("ONET_API_USERNAME")
        password = os.environ.get("ONET_API_PASSWORD")
        if not username or not password:
            raise NotImplementedError(
                "O*NET API integration requires ONET_API_USERNAME and "
                "ONET_API_PASSWORD environment variables. Register for free "
                "at https://services.onetcenter.org/"
            )
        raise NotImplementedError(
            "O*NET live API fetching is not yet implemented. "
            "Use the bundled O*NET skills data instead."
        )


class LinkedInApiFetcher:
    """Fetch skills from LinkedIn Skills API.

    LinkedIn's API requires OAuth app approval which is restrictive.
    This class documents the integration path for future implementation.
    """

    def fetch(self) -> list[str]:
        """Fetch skills from LinkedIn API.

        Raises:
            NotImplementedError: LinkedIn API requires OAuth app approval.
        """
        raise NotImplementedError(
            "LinkedIn Skills API integration requires OAuth app approval. "
            "Use the bundled LinkedIn skills data instead."
        )
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/unit/test_taxonomy.py::TestApiFetcherStubs -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/simple_resume/shell/ats/ tests/unit/test_taxonomy.py
git commit -m "feat: add shell-layer API fetcher stubs for O*NET and LinkedIn (#81, #82)"
```

## Chunk 5: Creative Language & Human Reviewer Mode (#62)

### Task 12: Add `ScoringMode` enum and constants

**Files:**

- Modify: `src/simple_resume/core/ats/constants.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/test_scoring_mode.py`:

```python
"""Tests for ScoringMode and human reviewer preset (#62)."""

from __future__ import annotations

import pytest

from tests.bdd import Scenario


class TestScoringModeConstants:
    """ScoringMode enum and weight presets."""

    def test_scoring_mode_enum_values(self, story: Scenario) -> None:
        story.given("the ScoringMode enum")
        from simple_resume.core.ats.constants import ScoringMode

        story.when("checking values")
        story.then("ATS and HUMAN_REVIEWER are available")
        assert ScoringMode.ATS.value == "ats"
        assert ScoringMode.HUMAN_REVIEWER.value == "human"

    def test_human_weights_sum_to_one(self, story: Scenario) -> None:
        story.given("human reviewer weight presets with BERT")
        from simple_resume.core.ats.constants import (
            HUMAN_BERT_WEIGHT,
            HUMAN_JACCARD_WEIGHT,
            HUMAN_KEYWORD_WEIGHT,
            HUMAN_TFIDF_WEIGHT,
        )

        story.when("summing the weights")
        total = (
            HUMAN_BERT_WEIGHT
            + HUMAN_TFIDF_WEIGHT
            + HUMAN_JACCARD_WEIGHT
            + HUMAN_KEYWORD_WEIGHT
        )

        story.then("they sum to 1.0")
        assert abs(total - 1.0) < 1e-9

    def test_human_fallback_weights_sum_to_one(self, story: Scenario) -> None:
        story.given("human reviewer weight presets without BERT")
        from simple_resume.core.ats.constants import (
            HUMAN_FALLBACK_JACCARD_WEIGHT,
            HUMAN_FALLBACK_KEYWORD_WEIGHT,
            HUMAN_FALLBACK_TFIDF_WEIGHT,
        )

        story.when("summing the fallback weights")
        total = (
            HUMAN_FALLBACK_TFIDF_WEIGHT
            + HUMAN_FALLBACK_JACCARD_WEIGHT
            + HUMAN_FALLBACK_KEYWORD_WEIGHT
        )

        story.then("they sum to 1.0")
        assert abs(total - 1.0) < 1e-9
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_scoring_mode.py::TestScoringModeConstants -v`
Expected: FAIL — `ScoringMode` doesn't exist

- [ ] **Step 3: Add ScoringMode and weight constants**

In `src/simple_resume/core/ats/constants.py`, add after `FALLBACK_KEYWORD_WEIGHT` (line 40):

```python
# Human Reviewer weights - emphasizes semantic similarity over term overlap
HUMAN_BERT_WEIGHT: Final[float] = 0.45
HUMAN_TFIDF_WEIGHT: Final[float] = 0.25
HUMAN_JACCARD_WEIGHT: Final[float] = 0.10
HUMAN_KEYWORD_WEIGHT: Final[float] = 0.20

# Human Reviewer fallback weights (no BERT)
HUMAN_FALLBACK_TFIDF_WEIGHT: Final[float] = 0.35
HUMAN_FALLBACK_JACCARD_WEIGHT: Final[float] = 0.15
HUMAN_FALLBACK_KEYWORD_WEIGHT: Final[float] = 0.50


class ScoringMode(str, Enum):
    """Scoring mode presets for tournament weight configuration."""

    ATS = "ats"
    HUMAN_REVIEWER = "human"
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_scoring_mode.py::TestScoringModeConstants -v`
Expected: PASS

### Task 13: Add `ScoringMode` to tournament

**Files:**

- Modify: `src/simple_resume/core/ats/tournament.py:100-180`

- [ ] **Step 1: Write failing test**

Add to `tests/unit/test_scoring_mode.py`:

```python
from simple_resume.core.ats.tournament import ATSTournament
from simple_resume.core.ats.constants import ScoringMode


class TestTournamentScoringMode:
    """ATSTournament uses ScoringMode for weight presets."""

    def test_default_mode_is_ats(self, story: Scenario) -> None:
        story.given("a tournament with no explicit mode")
        tournament = ATSTournament(include_bert=False)

        story.when("checking scorer weights")
        weights = [s.weight for s in tournament.scorers]

        story.then("ATS default weights are used")
        assert 0.40 in weights  # FALLBACK_TFIDF_WEIGHT

    def test_human_mode_changes_weights(self, story: Scenario) -> None:
        story.given("a tournament with HUMAN_REVIEWER mode")
        tournament = ATSTournament(
            include_bert=False, scoring_mode=ScoringMode.HUMAN_REVIEWER
        )

        story.when("checking scorer weights")
        weights = [s.weight for s in tournament.scorers]

        story.then("human reviewer weights are used")
        assert 0.35 in weights  # HUMAN_FALLBACK_TFIDF_WEIGHT
        assert 0.50 in weights  # HUMAN_FALLBACK_KEYWORD_WEIGHT

    def test_explicit_scorers_ignore_mode(self, story: Scenario) -> None:
        story.given("a tournament with explicit scorers and human mode")
        from simple_resume.core.ats.keyword import KeywordScorer

        custom = [KeywordScorer(weight=1.0)]
        tournament = ATSTournament(
            scorers=custom, scoring_mode=ScoringMode.HUMAN_REVIEWER
        )

        story.when("checking scorers")
        story.then("explicit scorers are used unchanged")
        assert len(tournament.scorers) == 1
        assert tournament.scorers[0].weight == 1.0

    def test_human_mode_enables_creative_expansion(self, story: Scenario) -> None:
        story.given("a tournament with HUMAN_REVIEWER mode")
        tournament = ATSTournament(
            include_bert=False, scoring_mode=ScoringMode.HUMAN_REVIEWER
        )

        story.when("checking keyword scorer config")
        keyword_scorer = [
            s for s in tournament.scorers if "keyword" in type(s).__name__.lower()
        ][0]

        story.then("creative expansion is enabled")
        assert keyword_scorer._config.enable_creative_expansion is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_scoring_mode.py::TestTournamentScoringMode -v`
Expected: FAIL — `scoring_mode` parameter doesn't exist

- [ ] **Step 3: Implement ScoringMode in tournament**

In `src/simple_resume/core/ats/tournament.py`:

Add imports:

```text
from simple_resume.core.ats.constants import (
    <existing imports>,
    HUMAN_BERT_WEIGHT,
    HUMAN_FALLBACK_JACCARD_WEIGHT,
    HUMAN_FALLBACK_KEYWORD_WEIGHT,
    HUMAN_FALLBACK_TFIDF_WEIGHT,
    HUMAN_JACCARD_WEIGHT,
    HUMAN_KEYWORD_WEIGHT,
    HUMAN_TFIDF_WEIGHT,
    ScoringMode,
)
from simple_resume.core.ats.keyword import KeywordScorer, KeywordScorerConfig
```

Update `__init__` (lines 100-121):

```python
def __init__(
    self,
    scorers: list[BaseScorer] | None = None,
    include_bert: bool = True,
    bert_model_name: str | None = None,
    scoring_mode: ScoringMode = ScoringMode.ATS,
) -> None:
    self._bert_model_name = bert_model_name
    self._scoring_mode = scoring_mode
    if scorers is None:
        self.scorers = self._create_default_scorers(include_bert=include_bert)
    else:
        self.scorers = scorers
```

Update `_create_default_scorers` (lines 123-181) to use mode-aware weights:

```python
def _create_default_scorers(self, include_bert: bool = True) -> list[BaseScorer]:
    scorers: list[BaseScorer] = []
    is_human = self._scoring_mode == ScoringMode.HUMAN_REVIEWER

    bert_available = False
    if include_bert:
        try:
            bert_scorer_cls = _import_bert_scorer()
            bert_weight = HUMAN_BERT_WEIGHT if is_human else DEFAULT_BERT_WEIGHT
            bert_scorer = bert_scorer_cls(
                weight=bert_weight,
                model_name=self._bert_model_name,
            )
            if bert_scorer.available:
                scorers.append(bert_scorer)
                bert_available = True
                logger.info("BERT scorer enabled with weight %.2f", bert_weight)
            else:
                logger.info("BERT scorer not available")
        except ImportError:
            logger.info("BERT module not available")

    # Select weights based on mode and BERT availability
    if bert_available:
        tfidf_w = HUMAN_TFIDF_WEIGHT if is_human else DEFAULT_TFIDF_WEIGHT
        jaccard_w = HUMAN_JACCARD_WEIGHT if is_human else DEFAULT_JACCARD_WEIGHT
        keyword_w = HUMAN_KEYWORD_WEIGHT if is_human else DEFAULT_KEYWORD_WEIGHT
    else:
        tfidf_w = HUMAN_FALLBACK_TFIDF_WEIGHT if is_human else FALLBACK_TFIDF_WEIGHT
        jaccard_w = (
            HUMAN_FALLBACK_JACCARD_WEIGHT if is_human else FALLBACK_JACCARD_WEIGHT
        )
        keyword_w = (
            HUMAN_FALLBACK_KEYWORD_WEIGHT if is_human else FALLBACK_KEYWORD_WEIGHT
        )

    # Build keyword scorer with creative expansion for human mode
    keyword_config = KeywordScorerConfig(
        enable_creative_expansion=is_human,
    )

    scorers.extend(
        [
            TFIDFScorer(weight=tfidf_w),
            JaccardScorer(weight=jaccard_w),
            KeywordScorer(weight=keyword_w, config=keyword_config),
        ]
    )

    return scorers
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/unit/test_scoring_mode.py -v`
Expected: PASS

- [ ] **Step 5: Export ScoringMode from `__init__.py`**

In `src/simple_resume/core/ats/__init__.py`, add `ScoringMode` import and export:

```python
from simple_resume.core.ats.constants import ScoringMode
```

Add `"ScoringMode"` to `__all__`.

- [ ] **Step 6: Commit**

```bash
git add src/simple_resume/core/ats/constants.py src/simple_resume/core/ats/tournament.py \
    src/simple_resume/core/ats/__init__.py tests/unit/test_scoring_mode.py
git commit -m "feat: add ScoringMode enum and human reviewer weight presets (#62)"
```

### Task 14: Add `--mode` CLI flag

**Files:**

- Modify: `src/simple_resume/shell/cli/main.py:255-305`
- Modify: `src/simple_resume/shell/cli/_screen.py:41-49,71-100`

- [ ] **Step 1: Write failing test**

Add to `tests/unit/test_scoring_mode.py`:

```python
class TestCliModeFlag:
    """--mode flag on sr screen command."""

    def test_mode_flag_accepted_by_parser(self, story: Scenario) -> None:
        story.given("the CLI argument parser")
        from simple_resume.shell.cli.main import create_parser

        parser = create_parser()

        story.when("parsing screen command with --mode human")
        args = parser.parse_args(["screen", "resume.txt", "job.txt", "--mode", "human"])

        story.then("mode is set to 'human'")
        assert args.mode == "human"

    def test_mode_default_is_ats(self, story: Scenario) -> None:
        story.given("the CLI argument parser")
        from simple_resume.shell.cli.main import create_parser

        parser = create_parser()

        story.when("parsing screen command without --mode")
        args = parser.parse_args(["screen", "resume.txt", "job.txt"])

        story.then("mode defaults to 'ats'")
        assert args.mode == "ats"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_scoring_mode.py::TestCliModeFlag -v`
Expected: FAIL — no `--mode` argument

- [ ] **Step 3: Add `--mode` to screen parser**

In `src/simple_resume/shell/cli/main.py`, add after the `--top` argument (line 305):

```python
screen_parser.add_argument(
    "--mode",
    choices=["ats", "human"],
    default="ats",
    help="Scoring mode: 'ats' for automated screening, 'human' for human reviewer "
    "(adjusts weights, enables creative term expansion)",
)
```

- [ ] **Step 4: Update `_build_tournament` and `handle_screen_command` to pass mode**

In `src/simple_resume/shell/cli/_screen.py`:

Update imports to include `ScoringMode`:

```text
from simple_resume.core.ats import (
    <existing imports>,
    ScoringMode,
)
```

Update `_build_tournament()`:

```python
def _build_tournament(
    scorers_selection: str,
    scoring_mode: ScoringMode = ScoringMode.ATS,
) -> ATSTournament:
    """Build a tournament with the selected scoring algorithms."""
    if scorers_selection == ScorerSelection.TFIDF:
        return ATSTournament(scorers=[TFIDFScorer(weight=1.0)])
    if scorers_selection == ScorerSelection.JACCARD:
        return ATSTournament(scorers=[JaccardScorer(weight=1.0)])
    if scorers_selection == ScorerSelection.KEYWORD:
        kw_config = KeywordScorerConfig(
            enable_creative_expansion=(scoring_mode == ScoringMode.HUMAN_REVIEWER),
        )
        return ATSTournament(scorers=[KeywordScorer(weight=1.0, config=kw_config)])
    return ATSTournament(scoring_mode=scoring_mode)
```

Add `KeywordScorerConfig` to imports from `simple_resume.core.ats`.

In `handle_screen_command()`, read mode and pass it:

```python
mode_str: str = getattr(args, "mode", "ats")
scoring_mode = ScoringMode(mode_str)
...
tournament = _build_tournament(scorers_selection, scoring_mode=scoring_mode)
```

- [ ] **Step 5: Run all tests**

Run: `uv run pytest tests/unit/test_scoring_mode.py tests/unit/test_cli_ats.py tests/unit/test_cli_screen_batch.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/simple_resume/shell/cli/main.py src/simple_resume/shell/cli/_screen.py \
    tests/unit/test_scoring_mode.py
git commit -m "feat: add --mode flag for human reviewer scoring mode (#62)"
```

## Chunk 6: Version Bump & Finalization

### Task 15: Version bump and CHANGELOG

**Files:**

- Modify: `pyproject.toml:33`
- Modify: `src/simple_resume/__init__.py`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Bump version to 0.3.2**

In `pyproject.toml` line 33: `version = "0.3.2"`

In `src/simple_resume/__init__.py`: update `__version__ = "0.3.2"`

- [ ] **Step 2: Add CHANGELOG entry**

Prepend to `CHANGELOG.md`:

```markdown
## [0.3.2] - 2026-03-11

### Added
- Batch screening now supports `--format json`, `--format yaml`, and `--verbose` flags (#105)
- PDF text extraction via pdfplumber for ATS screening (#104)
- HTML/HTM text extraction via BeautifulSoup for ATS screening (#104)
- O*NET skills taxonomy data bundle with 400+ technology skills (#81)
- LinkedIn skills taxonomy data bundle with 400+ professional skills (#82)
- Merged skills pipeline: hardcoded + O*NET + LinkedIn bundles (#81, #82)
- Shell-layer API fetcher stubs for O*NET and LinkedIn (#81, #82)
- `--mode {ats,human}` flag for human reviewer scoring mode (#62)
- `ScoringMode` enum with configurable tournament weight presets (#62)
- Creative term expansion enabled by default in human reviewer mode (#62)

### Fixed
- Latin-1 encoding fallback now emits a UserWarning (#101)
- Report file write errors handled gracefully with stderr message (#102)

### Changed
- `pdfplumber` and `beautifulsoup4` are now core dependencies (#104)
- `_collect_resume_files` docstring corrected (#103)
- Batch test helper uses `argparse.Namespace` instead of custom class (#103)
- `linkedin` optional extra removed (beautifulsoup4 moved to core) (#104)
```

- [ ] **Step 3: Run full test suite**

Run: `uv run pytest --quiet`
Expected: PASS with >85% coverage

- [ ] **Step 4: Run quality gates**

Run: `uv run ruff check src/ tests/ && uv run mypy src/`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/simple_resume/__init__.py CHANGELOG.md uv.lock
git commit -m "chore: bump version to 0.3.2"
```

### Task 16: Final validation

- [ ] **Step 1: Run complete test suite with coverage**

Run: `uv run pytest --tb=short`
Expected: All tests pass, coverage >85%

- [ ] **Step 2: Run pre-commit hooks**

Run: `uv run pre-commit run --all-files`
Expected: All hooks pass

- [ ] **Step 3: Verify wheel builds**

Run: `uv build --quiet && uv run pip install dist/*.whl --quiet`
Expected: Clean build and install
