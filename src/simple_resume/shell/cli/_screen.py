"""ATS screening display and file-reading helpers for the CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from simple_resume.core.ats import (
    ATSReportGenerator,
    ATSTournament,
    JaccardScorer,
    KeywordScorer,
    ScorerSelection,
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


_RESUME_SUFFIXES = {".txt", ".md", ".yaml", ".yml", ".json"}


def _build_tournament(scorers_selection: str) -> ATSTournament:
    """Build a tournament with the selected scoring algorithms."""
    if scorers_selection == ScorerSelection.TFIDF:
        return ATSTournament(scorers=[TFIDFScorer(weight=1.0)])
    if scorers_selection == ScorerSelection.JACCARD:
        return ATSTournament(scorers=[JaccardScorer(weight=1.0)])
    if scorers_selection == ScorerSelection.KEYWORD:
        return ATSTournament(scorers=[KeywordScorer(weight=1.0)])
    return ATSTournament()


def _collect_resume_files(directory: Path) -> list[Path]:
    """Collect readable resume files from a directory."""
    return sorted(
        p
        for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in _RESUME_SUFFIXES
    )


def _output_report(content: str, output_path: Path | None) -> None:
    """Print or save a report."""
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        print(f"Report saved to: {output_path}")
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

    try:
        # Read job description
        job_text = _read_file_text(job_path)
        if not job_text.strip():
            print(f"Error: Job description file is empty: {job_path}")
            return 1

        tournament = _build_tournament(scorers_selection)

        # Batch mode: screen all resumes in a directory
        if batch:
            return _handle_batch(
                resume_path,
                job_path,
                job_text,
                tournament,
                top_n,
                output_path,
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


def _handle_batch(  # noqa: PLR0913
    resume_path: Path,
    job_path: Path,
    job_text: str,
    tournament: ATSTournament,
    top_n: int | None,
    output_path: Path | None,
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

    # Score each resume
    results: list[tuple[str, float]] = []
    for rfile in resume_files:
        try:
            text = _read_file_text(rfile)
        except (OSError, SimpleResumeError) as exc:
            print(f"  Skipping {rfile.name}: {exc}")
            continue
        if not text.strip():
            continue
        score = tournament.score(text, job_text).overall_score
        results.append((rfile.name, score))

    if not results:
        print("Error: No resume files could be read.")
        return 1

    # Apply top-N limit (sorting is done inside _format_batch_report)
    if top_n is not None and top_n > 0:
        results = sorted(results, key=lambda x: x[1], reverse=True)[:top_n]

    report = _format_batch_report(results, str(job_path))
    _output_report(report, output_path)
    return 0


def _read_file_text(file_path: Path) -> str:
    """Read text content from a file, handling various formats."""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = file_path.suffix.lower()

    # PDF/HTML file formats are not yet supported for job descriptions
    # Provide user-friendly error with guidance on supported formats
    if suffix in [".pdf", ".html", ".htm"]:
        raise ValidationError(
            f"Job description file format '{suffix}' is not yet supported",
            errors=[
                f"Cannot read '{file_path.name}' - "
                "PDF/HTML parsing is planned for a future release",
                "Supported formats: .txt, .md, .yaml, .json",
            ],
            context={"file_path": str(file_path), "format": suffix},
            filename=str(file_path),
        )

    # Read text content
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Try with different encoding
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


def _format_batch_report(results: list[tuple[str, float]], job_file: str) -> str:
    """Format batch screening results as a ranked report."""
    results = sorted(results, key=lambda x: x[1], reverse=True)
    lines = [
        "=" * 60,
        "BATCH ATS SCREENING REPORT",
        "=" * 60,
        "",
        f"Job description: {job_file}",
        f"Resumes scored:  {len(results)}",
        "",
        "-" * 60,
        "RANKED RESULTS",
        "-" * 60,
        "",
    ]

    for rank, (name, score) in enumerate(results, 1):
        score_100 = score * 100
        status = _get_status_label(score_100)
        lines.append(f"{rank}. {name:40s} {score_100:5.1f}/100  {status}")

    lines.extend(["", "=" * 60])
    return "\n".join(lines)


def _get_status_label(score: float) -> str:
    """Get status label based on score (0-100 scale)."""
    if score >= _EXCELLENT_THRESHOLD:
        return "Excellent - Strong match!"
    elif score >= _GOOD_THRESHOLD:
        return "Good - Competitive candidate."
    elif score >= _FAIR_THRESHOLD:
        return "Fair - Consider improvements."
    elif score >= _POOR_THRESHOLD:
        return "Poor - Significant gaps."
    else:
        return "Very Poor - Not a match."
