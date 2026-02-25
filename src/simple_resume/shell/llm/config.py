"""API key resolution and LLM configuration factory.

Resolves API keys from CLI arguments and environment variables,
creating LLMConfig instances for provider initialization.
"""

from __future__ import annotations

import os

from simple_resume.core.llm.protocol import LLMConfig

# Environment variables checked in priority order
_ENV_KEY_NAMES = [
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "MISTRAL_API_KEY",
    "COHERE_API_KEY",
]


def resolve_api_key(cli_key: str | None = None) -> str | None:
    """Resolve an API key from CLI argument or environment variables.

    Priority order:
    1. Explicit CLI argument (if non-empty)
    2. Environment variables (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)

    Args:
        cli_key: API key passed via CLI --api-key argument.

    Returns:
        The resolved API key, or None if not found.

    """
    if cli_key and cli_key.strip():
        return cli_key.strip()

    for env_name in _ENV_KEY_NAMES:
        value = os.environ.get(env_name)
        if value and value.strip():
            return value.strip()

    return None


def resolve_llm_config(
    api_key: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> LLMConfig:
    """Create an LLMConfig by resolving API key and applying defaults.

    Args:
        api_key: Explicit API key (takes priority over env vars).
        model: Model identifier override.
        temperature: Temperature override.
        max_tokens: Max tokens override.

    Returns:
        Fully resolved LLMConfig.

    Raises:
        ValueError: If no API key can be resolved.

    """
    resolved_key = resolve_api_key(cli_key=api_key)
    if not resolved_key:
        raise ValueError(
            "No API key found. Provide --api-key or set an environment variable "
            "(OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)"
        )

    return LLMConfig(
        api_key=resolved_key,
        model=model if model is not None else "claude-sonnet-4-20250514",
        temperature=temperature if temperature is not None else 0.3,
        max_tokens=max_tokens if max_tokens is not None else 4096,
    )


__all__ = ["resolve_api_key", "resolve_llm_config"]
