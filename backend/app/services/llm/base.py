"""LLM provider interfaces for AI generation"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for Large Language Model providers"""

    @property
    def is_configured(self) -> bool:
        """Whether the provider is properly configured (e.g., API key available)."""
        ...

    async def generate(self, prompt: str) -> str:
        """Generate a response for the given prompt.

        Should return plain text.
        Should handle provider-specific retries/backoff and return a friendly
        user-facing message on rate-limit or failure instead of raising.
        """
        ...
