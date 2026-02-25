"""Shell LLM layer (I/O, API calls, side effects)."""

from simple_resume.shell.llm.gate import is_llm_available, requires_llm

__all__ = [
    "is_llm_available",
    "requires_llm",
]
