"""
Abstract base class that every provider must implement.
The rest of the application ONLY calls BaseProvider methods — never SDK calls directly.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional


class BaseProvider(ABC):
    """Common interface for all AI model providers."""

    provider_name: str = "base"

    @abstractmethod
    def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Send a prompt to the model and return the text response.

        Args:
            prompt: The user-facing message or instruction.
            model: Provider-specific model identifier string.
            system_prompt: Optional system-level instruction prepended to the exchange.
            temperature: Sampling temperature; higher = more creative.
            max_tokens: Upper bound on response length in tokens.

        Returns:
            Generated text content as a plain string.

        Raises:
            ProviderError: On API failure, timeout, or auth issues.
        """

    @abstractmethod
    def list_models(self) -> List[str]:
        """Return the list of models available for this provider."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider_name!r})"


class ProviderError(Exception):
    """Raised when a provider call fails for any reason."""
