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

# Score threshold constants
_EXCELLENT_THRESHOLD = 80
_GOOD_THRESHOLD = 65
_FAIR_THRESHOLD = 50
_POOR_THRESHOLD = 35
_PASSING_THRESHOLD = 0.5


def handle_screen_command(args: argparse.Namespace) -> int:  # noqa: PLR0912
    """Screen resume against job description using ATS scoring."""
    from simple_resume.shell.cli.main import _handle_unexpected_error  # noqa: PLC0415

    resume_path: Path = args.resume
    job_path: Path = args.job
    output_path: Path | None = getattr(args, "output", None)
    report_format: str = getattr(args, "format", "text")
    scorers_selection: str = getattr(args, "scorers", "all")
    verbose: bool = getattr(args, "verbose", False)

    try:
        # Read resume text
        resume_text = _read_file_text(resume_path)
        if not resume_text.strip():
            print(f"Error: Resume file is empty or could not be read: {resume_path}")
            return 1

        # Read job description
        job_text = _read_file_text(job_path)
        if not job_text.strip():
            msg = f"Error: Job description file is empty: {job_path}"
            print(msg)
            return 1

        # Configure scorers based on selection
        if scorers_selection == ScorerSelection.ALL:
            tournament = ATSTournament()  # Uses default scorers
        elif scorers_selection == ScorerSelection.TFIDF:
            tournament = ATSTournament(scorers=[TFIDFScorer(weight=1.0)])
        elif scorers_selection == ScorerSelection.JACCARD:
            tournament = ATSTournament(scorers=[JaccardScorer(weight=1.0)])
        elif scorers_selection == ScorerSelection.KEYWORD:
            tournament = ATSTournament(scorers=[KeywordScorer(weight=1.0)])
        else:
            tournament = ATSTournament()

        # Run tournament
        result = tournament.score(resume_text, job_text)

        # Generate report
        generator = ATSReportGenerator(
            result,
            resume_file=str(resume_path),
            job_file=str(job_path),
        )

        # Output based on format
        if report_format == "yaml":
            report_content = generator.generate_yaml()
        elif report_format == "json":
            report_content = generator.generate_json()
        else:  # text format
            report_content = _format_text_report(result, verbose)

        # Save or print
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report_content)
            print(f"Report saved to: {output_path}")
        else:
            print(report_content)

        # Return exit code based on score
        # Score 50+/100 is considered passing
        return 0 if result.overall_score >= _PASSING_THRESHOLD else 1

    except SimpleResumeError as exc:
        print(f"Screening error: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - safety net
        return _handle_unexpected_error(exc, "ATS screening")


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
