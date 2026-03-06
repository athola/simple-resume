"""LiteLLM wrapper implementing the LLMProvider protocol.

This module handles actual API calls to LLM providers via litellm.
It belongs in the shell layer because it performs I/O.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from simple_resume.core.exceptions import LLMError
from simple_resume.core.llm.protocol import LLMConfig, LLMProvider

logger = logging.getLogger(__name__)


class LiteLLMProvider(LLMProvider):
    """LLM provider backed by litellm for multi-provider support.

    Wraps litellm.completion() to provide a consistent interface
    across OpenAI, Anthropic, and other providers.

    Attributes:
        config: The LLM configuration (model, API key, etc.).

    """

    def __init__(self, config: LLMConfig) -> None:
        """Initialize with LLM configuration.

        Args:
            config: LLM configuration including API key and model.

        """
        self.config = config

    def complete(self, prompt: str, system: str = "", **kwargs: Any) -> str:
        """Send a completion request and return the text response.

        Args:
            prompt: The user prompt.
            system: Optional system prompt.
            **kwargs: Additional parameters passed to litellm.

        Returns:
            The text content of the LLM response.

        Raises:
            LLMError: If the API call fails.

        """
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            import litellm as _litellm  # noqa: PLC0415  # ty: ignore[unresolved-import]  # pyright: ignore[reportMissingImports]

            response = _litellm.completion(
                model=self.config.model,
                messages=messages,
                api_key=self.config.api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                **kwargs,
            )
            content = response.choices[0].message.content
            if content is None:
                raise LLMError(
                    "LLM returned empty response",
                    provider="litellm",
                    model=self.config.model,
                )
            return content  # type: ignore[no-any-return]
        except ImportError as exc:  # pragma: no cover
            raise LLMError(
                "litellm is not installed. "
                "Install with: pip install simple-resume[llm]",
                provider="litellm",
                model=self.config.model,
            ) from exc
        except Exception as exc:
            raise LLMError(
                f"{type(exc).__name__}: {exc}",
                provider="litellm",
                model=self.config.model,
            ) from exc

    def complete_structured(
        self, prompt: str, schema: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Send a completion request expecting a JSON-structured response.

        Instructs the LLM to respond in JSON format and parses the result.

        Args:
            prompt: The user prompt.
            schema: JSON schema describing the expected response structure.
            **kwargs: Additional parameters passed to litellm.

        Returns:
            Parsed dictionary from the LLM JSON response.

        Raises:
            LLMError: If the API call fails or response is not valid JSON.

        """
        json_prompt = (
            f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n"
            f"{json.dumps(schema, indent=2)}"
        )

        raw = self.complete(json_prompt, **kwargs)

        try:
            return json.loads(raw)  # type: ignore[no-any-return]
        except json.JSONDecodeError as exc:
            raise LLMError(
                f"LLM response was not valid JSON: {exc}",
                provider="litellm",
                model=self.config.model,
            ) from exc


__all__ = ["LiteLLMProvider"]
