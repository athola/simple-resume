"""Job post tailoring CLI handler.

Performs gap analysis between a resume and a job posting, optionally
using an LLM to produce tailored suggestions.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from simple_resume.core.ats.tailor import (
    JobRequirements,
    analyze_gaps,
    build_tailoring_prompt,
)
from simple_resume.core.exceptions import LLMError, SimpleResumeError


def _load_resume_yaml(resume_path: Path) -> dict[str, object]:
    """Load a resume YAML file and return the parsed dict."""
    if not resume_path.exists():
        raise FileNotFoundError(f"Resume file not found: {resume_path}")
    return yaml.safe_load(resume_path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _load_job_posting(job_path: Path) -> str:
    """Read a job posting file as plain text."""
    if not job_path.exists():
        raise FileNotFoundError(f"Job posting file not found: {job_path}")
    return job_path.read_text(encoding="utf-8")


def _extract_requirements_from_text(job_text: str) -> JobRequirements:
    """Build a minimal JobRequirements from raw job posting text.

    Extracts the first non-empty line as the title and treats the
    full text as keywords for gap analysis.
    """
    lines = [line.strip() for line in job_text.strip().split("\n") if line.strip()]
    title = lines[0] if lines else "Unknown Position"
    # Use all non-empty lines as keywords for basic matching
    keywords = [line for line in lines[1:] if len(line) > 3]  # noqa: PLR2004
    return JobRequirements(title=title, keywords=keywords)


def handle_tailor_command(args: argparse.Namespace) -> int:
    """Tailor a resume to a job posting using gap analysis and optional LLM.

    Args:
        args: Parsed CLI arguments containing ``resume``, ``job``,
            and optional ``api_key``, ``model``, ``report`` flags.

    Returns:
        Exit code (0 for success, non-zero for failure).

    """
    from simple_resume.shell.cli.main import _handle_unexpected_error  # noqa: PLC0415

    resume_path: Path = args.resume
    job_path: Path = args.job
    api_key: str | None = getattr(args, "api_key", None)
    model: str | None = getattr(args, "model", None)
    report_only: bool = getattr(args, "report", False)

    try:
        # Load inputs
        resume_data = _load_resume_yaml(resume_path)
        job_text = _load_job_posting(job_path)

        # Run gap analysis
        requirements = _extract_requirements_from_text(job_text)
        gap = analyze_gaps(resume_data, requirements)

        # Always print the gap report
        print(gap.summary)
        print()

        if report_only:
            return 0

        # LLM tailoring (requires --api-key or env var)
        return _run_llm_tailoring(
            resume_data, job_text, gap, api_key, model, resume_path
        )

    except (FileNotFoundError, ValueError) as exc:
        print(f"Tailor error: {exc}")
        return 1
    except SimpleResumeError as exc:
        print(f"Tailor error: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - safety net
        return _handle_unexpected_error(exc, "resume tailoring")


def _run_llm_tailoring(  # noqa: PLR0913
    resume_data: dict[str, object],
    job_text: str,
    gap: object,
    api_key: str | None,
    model: str | None,
    resume_path: Path,
) -> int:
    """Run LLM-based tailoring if an API key is available.

    Args:
        resume_data: Parsed resume dict.
        job_text: Raw job posting text.
        gap: Gap analysis result (for context).
        api_key: Explicit API key or None.
        model: Model identifier override or None.
        resume_path: Original resume file path (for output naming).

    Returns:
        Exit code (0 for success, non-zero for failure).

    """
    from simple_resume.shell.llm.config import resolve_api_key  # noqa: PLC0415

    resolved_key = resolve_api_key(cli_key=api_key)
    if not resolved_key:
        print(
            "No API key found. Provide --api-key or set OPENAI_API_KEY / "
            "ANTHROPIC_API_KEY to enable LLM tailoring."
        )
        print("Run with --report for gap analysis only.")
        return 1

    try:
        from simple_resume.shell.llm.config import (  # noqa: PLC0415
            resolve_llm_config,
        )
        from simple_resume.shell.llm.gate import (  # noqa: PLC0415
            is_llm_available,
        )

        if not is_llm_available():
            print(
                "LLM features require the [llm] extra: pip install simple-resume[llm]"
            )
            return 1

        from simple_resume.shell.llm.client import (  # noqa: PLC0415
            LiteLLMProvider,
        )

        config = resolve_llm_config(api_key=resolved_key, model=model)
        provider = LiteLLMProvider(config)

        prompt = build_tailoring_prompt(resume_data, job_text)
        result = provider.complete(prompt)

        # Write tailored output
        output_path = resume_path.with_name(
            f"{resume_path.stem}_tailored{resume_path.suffix}"
        )
        output_path.write_text(result, encoding="utf-8")
        print(f"Tailored resume saved: {output_path}")
        return 0

    except LLMError as exc:
        print(f"LLM error: {exc}")
        return 1


__all__ = ["handle_tailor_command"]
