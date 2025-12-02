"""PDF execution for the shell layer.

This module provides functions to execute PDF generation
effects created by the core layer.
It implements the "imperative shell" pattern,
performing actual I/O operations.
"""

from pathlib import Path

from simple_resume.core.effects import Effect
from simple_resume.core.result import GenerationMetadata, GenerationResult
from simple_resume.shell.effect_executor import EffectExecutor


def execute_pdf_generation(
    pdf_content: bytes,
    effects: list[Effect],
    output_path: Path,
    metadata: GenerationMetadata,
) -> GenerationResult:
    """Execute PDF generation by running effects and returning result.

    This function performs I/O operations by executing the provided effects.
    It uses the EffectExecutor to run all effects in sequence.

    Args:
        pdf_content: PDF content as bytes (for reference/validation)
        effects: List of effects to execute (MakeDirectory, WriteFile, etc.)
        output_path: Target PDF file path
        metadata: Generation metadata to include in result

    Returns:
        GenerationResult with output path and metadata

    Raises:
        Various I/O exceptions from effect execution

    """
    # Create executor and run all effects
    executor = EffectExecutor()
    executor.execute_many(effects)

    # Return result
    return GenerationResult(
        output_path=output_path,
        format_type="pdf",
        metadata=metadata,
    )


__all__ = ["execute_pdf_generation"]
