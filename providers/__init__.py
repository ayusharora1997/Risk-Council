"""
Provider registry — the single place where providers are looked up by name.
Import from here rather than instantiating providers directly.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Type

from .base_provider import BaseProvider, ProviderError
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .openrouter_provider import OpenRouterProvider
from .ollama_provider import OllamaProvider

_REGISTRY: Dict[str, Type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "openrouter": OpenRouterProvider,
    "ollama": OllamaProvider,
}

AVAILABLE_PROVIDERS: List[str] = list(_REGISTRY.keys())

PROVIDER_DEFAULT_MODELS: Dict[str, List[str]] = {
    "openai": OpenAIProvider.DEFAULT_MODELS,
    "anthropic": AnthropicProvider.DEFAULT_MODELS,
    "gemini": GeminiProvider.DEFAULT_MODELS,
    "openrouter": OpenRouterProvider.DEFAULT_MODELS,
    "ollama": OllamaProvider.DEFAULT_MODELS,
}


def get_provider(provider_name: str) -> BaseProvider:
    """Instantiate a provider using environment-variable API keys."""
    cls = _REGISTRY.get(provider_name.lower())
    if cls is None:
        raise ProviderError(
            f"Unknown provider '{provider_name}'. Available: {AVAILABLE_PROVIDERS}"
        )
    return cls()


def get_provider_with_keys(
    provider_name: str,
    api_keys: Optional[Dict[str, str]] = None,
) -> BaseProvider:
    """Instantiate a provider using caller-supplied keys, falling back to env vars.

    Args:
        provider_name: One of the AVAILABLE_PROVIDERS strings.
        api_keys: Dict mapping provider names to API key strings.
                  Keys absent from the dict fall back to env vars.
    """
    name = provider_name.lower()
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ProviderError(
            f"Unknown provider '{provider_name}'. Available: {AVAILABLE_PROVIDERS}"
        )

    supplied_key: Optional[str] = None
    if api_keys:
        supplied_key = api_keys.get(name) or api_keys.get(f"{name}_api_key") or None

    if name == "ollama":
        return cls()  # no API key needed

    return cls(api_key=supplied_key or None)


__all__ = [
    "BaseProvider",
    "ProviderError",
    "OpenAIProvider",
    "AnthropicProvider",
    "GeminiProvider",
    "OpenRouterProvider",
    "OllamaProvider",
    "AVAILABLE_PROVIDERS",
    "PROVIDER_DEFAULT_MODELS",
    "get_provider",
    "get_provider_with_keys",
]
