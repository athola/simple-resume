"""Protocol definitions for LLM providers.

Defines the abstract interface that all LLM providers must implement,
plus the configuration dataclass. This module is pure (no I/O, no API keys).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for an LLM provider.

    Attributes:
        api_key: The API key for authentication.
        model: The model identifier (e.g., "claude-sonnet-4-20250514").
        temperature: Sampling temperature (0.0 to 1.0).
        max_tokens: Maximum tokens in the response.

    """

    api_key: str = field(repr=False)
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.3
    max_tokens: int = 4096


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM integrations must implement this interface, enabling
    dependency injection and testability via mock providers.
    """

    @abstractmethod
    def complete(self, prompt: str, system: str = "", **kwargs: Any) -> str:
        """Send a completion request and return the text response.

        Args:
            prompt: The user prompt.
            system: Optional system prompt.
            **kwargs: Provider-specific parameters.

        Returns:
            The text content of the LLM response.

        """

    @abstractmethod
    def complete_structured(
        self, prompt: str, schema: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Send a completion request expecting a JSON-structured response.

        Args:
            prompt: The user prompt.
            schema: JSON schema describing the expected response structure.
            **kwargs: Provider-specific parameters.

        Returns:
            Parsed dictionary from the LLM JSON response.

        """


__all__ = ["LLMConfig", "LLMProvider"]
