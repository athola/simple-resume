"""ATS screening display and file-reading helpers for the CLI."""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path

import oyaml as yaml

from simple_resume.core.ats import (
    ATSReportGenerator,
    ATSTournament,
    JaccardScorer,
    KeywordScorer,
    KeywordScorerConfig,
    ScorerSelection,
    ScoringMode,
    TFIDFScorer,
    TournamentResult,
)
from simple_resume.core.exceptions import SimpleResumeError, ValidationError
from simple_resume.shell.cli._errors import _handle_unexpected_error

# Score threshold constants
_EXCELLENT_THRESHOLD = 80
_GOOD_THRESHOLD = 65
_FAIR_THRESHOLD = 50
_POOR_THRESHOLD = 35
_PASSING_THRESHOLD = 0.5


_RESUME_SUFFIXES = {".txt", ".md", ".yaml", ".yml", ".json", ".pdf", ".html", ".htm"}


@dataclass(frozen=True)
class _BatchDisplayOpts:
    """Display and output options for batch screening."""

    top_n: int | None = None
    output_path: Path | None = None
    report_format: str = "text"
    verbose: bool = False


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
        is_human = scoring_mode == ScoringMode.HUMAN_REVIEWER
        kw_config = KeywordScorerConfig(
            enable_creative_expansion=is_human,
        )
        return ATSTournament(scorers=[KeywordScorer(weight=1.0, config=kw_config)])
    return ATSTournament(scoring_mode=scoring_mode)


def _collect_resume_files(directory: Path) -> list[Path]:
    """Collect resume files with supported suffixes from a directory."""
    return sorted(
        p
        for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in _RESUME_SUFFIXES
    )


def _output_report(content: str, output_path: Path | None) -> None:
    """Print or save a report."""
    if output_path:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            print(f"Report saved to: {output_path}")
        except OSError as exc:
            print(
                f"Error: report could not be saved to '{output_path}': {exc}",
                file=sys.stderr,
            )
    else:
        print(content)


def handle_screen_command(args: argparse.Namespace) -> int:  # noqa: PLR0912
    """Screen resume(s) against job description using ATS scoring."""
    resume_path: Path = args.resume
    job_path: Path = args.job
    output_path: Path | None = getattr(args, "output", None)
    report_format: str = getattr(args, "format", "text")
    scorers_selection: str = getattr(args, "scorers", "all")
    verbose: bool = getattr(args, "verbose", False)
    batch: bool = getattr(args, "batch", False)
    top_n: int | None = getattr(args, "top", None)

    mode_str: str = getattr(args, "mode", "ats")
    scoring_mode = ScoringMode(mode_str)

    try:
        # Read job description
        job_text = _read_file_text(job_path)
        if not job_text.strip():
            print(f"Error: Job description file is empty: {job_path}")
            return 1

        tournament = _build_tournament(scorers_selection, scoring_mode=scoring_mode)

        # Batch mode: screen all resumes in a directory
        if batch:
            display = _BatchDisplayOpts(
                top_n=top_n,
                output_path=output_path,
                report_format=report_format,
                verbose=verbose,
            )
            return _handle_batch(
                resume_path,
                job_path,
                job_text,
                tournament,
                display,
            )

        # Single mode: screen one resume
        resume_text = _read_file_text(resume_path)
        if not resume_text.strip():
            print(f"Error: Resume file is empty or could not be read: {resume_path}")
            return 1

        result = tournament.score(resume_text, job_text)

        generator = ATSReportGenerator(
            result,
            resume_file=str(resume_path),
            job_file=str(job_path),
        )

        if report_format == "yaml":
            report_content = generator.generate_yaml()
        elif report_format == "json":
            report_content = generator.generate_json()
        else:
            report_content = _format_text_report(result, verbose)

        _output_report(report_content, output_path)
        return 0 if result.overall_score >= _PASSING_THRESHOLD else 1

    except SimpleResumeError as exc:
        print(f"Screening error: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - safety net
        return _handle_unexpected_error(exc, "ATS screening")


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
    return str(soup.get_text(separator="\n"))


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
            f"File '{file_path.name}' is not valid UTF-8, falling back to latin-1 "
            "encoding. Check the file encoding if text appears garbled.",
            UserWarning,
            stacklevel=2,
        )
        return file_path.read_text(encoding="latin-1")


def _collect_ats_warnings(result: TournamentResult) -> list[str]:
    """Collect warning messages from ATS scoring results.

    Extracts 'error' keys from ScorerResult.details that indicate
    non-fatal issues like sklearn fallbacks or empty input handling.

    Args:
        result: Tournament result containing algorithm results

    Returns:
        List of warning messages to display to users

    """
    warnings = []

    # Check each algorithm result for error details
    for alg_result in result.algorithm_results:
        error = alg_result.details.get("error")
        if error:
            warnings.append(f"{alg_result.name}: {error}")

    # Check tournament-level metadata for errors
    if "error" in result.metadata:
        warnings.append(f"Tournament: {result.metadata['error']}")

    return warnings


def _format_text_report(result: TournamentResult, verbose: bool = False) -> str:
    """Format tournament result as human-readable text."""
    score_100 = result.overall_score * 100

    lines = [
        "=" * 60,
        "ATS SCORING REPORT",
        "=" * 60,
        "",
        f"Overall Score: {score_100:.1f}/100",
        f"Normalized:   {result.overall_score:.4f}",
        "",
        f"Status: {_get_status_label(score_100)}",
        "",
        "-" * 60,
        "ALGORITHM BREAKDOWN",
        "-" * 60,
    ]

    for alg_result in result.algorithm_results:
        lines.extend(
            [
                "",
                f"{alg_result.name}:",
                f"  Score:    {alg_result.score * 100:.1f}/100",
                f"  Weight:   {alg_result.weight}",
                f"  Weighted: {alg_result.weighted_score * 100:.1f}/100",
            ]
        )

        if verbose and "cosine_similarity" in alg_result.details:
            lines.append(f"  Cosine:   {alg_result.details['cosine_similarity']:.4f}")

        if verbose and "shared_keywords" in alg_result.details:
            shared = alg_result.details["shared_keywords"]
            if shared:
                lines.append(f"  Shared:   {len(shared)} keywords/phrases")

    if verbose and result.component_breakdown:
        lines.extend(
            [
                "",
                "-" * 60,
                "COMPONENT SCORES",
                "-" * 60,
            ]
        )
        for component, score in result.component_breakdown.items():
            lines.append(f"{component}: {score:.4f}")

    # Collect warnings from algorithm results (issue #58)
    warnings = _collect_ats_warnings(result)
    if warnings:
        lines.extend(
            [
                "",
                "-" * 60,
                "WARNINGS",
                "-" * 60,
            ]
        )
        for warning in warnings:
            lines.append(f"  * {warning}")

    # Show failed scorers if any
    if result.failed_scorers:
        lines.extend(
            [
                "",
                "-" * 60,
                "FAILED SCORERS",
                "-" * 60,
            ]
        )
        for scorer_name, error_msg in result.failed_scorers:
            if verbose:
                lines.append(f"  * {scorer_name}: {error_msg}")
            else:
                lines.append(f"  * {scorer_name} (use --verbose for details)")

    lines.extend(
        [
            "",
            "=" * 60,
        ]
    )

    return "\n".join(lines)


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
    yaml_output: str = yaml.dump(data, default_flow_style=False, allow_unicode=True)
    return yaml_output


def _get_status_label(score: float) -> str:
    """Get status label based on score (0-100 scale)."""
    if score >= _EXCELLENT_THRESHOLD:
        return "Excellent - Strong match!"
    if score >= _GOOD_THRESHOLD:
        return "Good - Competitive candidate."
    if score >= _FAIR_THRESHOLD:
        return "Fair - Consider improvements."
    if score >= _POOR_THRESHOLD:
        return "Poor - Significant gaps."
    return "Very Poor - Not a match."
