"""Feature gating for LLM-dependent functionality.

Provides a decorator and utility to check whether the optional [llm]
dependency (litellm) is installed, raising a clear error when it is not.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, TypeVar

from simple_resume.core.exceptions import LLMNotAvailableError

F = TypeVar("F", bound=Callable[..., Any])


def is_llm_available() -> bool:
    """Check if the litellm package is installed.

    Returns:
        True if litellm can be imported, False otherwise.

    """
    try:
        import litellm  # noqa: F401  # ty: ignore[unresolved-import]

        return True
    except ImportError:
        return False


def requires_llm(func: F) -> F:
    """Decorate a function to gate it behind the [llm] optional dependency.

    If litellm is not installed, raises LLMNotAvailableError with
    a clear install hint instead of an obscure ImportError.

    Args:
        func: The function to gate.

    Returns:
        Wrapped function that checks LLM availability before execution.

    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not is_llm_available():
            raise LLMNotAvailableError(
                "LLM features require the [llm] extra: pip install simple-resume[llm]",
                install_hint="pip install simple-resume[llm]",
            )
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


__all__ = ["is_llm_available", "requires_llm"]
