"""Anthropic provider — Claude Opus, Sonnet, Haiku families."""
from __future__ import annotations

import os
from typing import List, Optional

import anthropic
from anthropic import APIError

from .base_provider import BaseProvider, ProviderError


class AnthropicProvider(BaseProvider):
    provider_name = "anthropic"

    DEFAULT_MODELS: List[str] = [
        "claude-opus-4-8",
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
    ]

    def __init__(self, api_key: Optional[str] = None) -> None:
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ProviderError(
                "Anthropic API key missing. Set the ANTHROPIC_API_KEY environment variable."
            )
        self.client = anthropic.Anthropic(api_key=key)

    def generate(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-6",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            response = self.client.messages.create(**kwargs)
            return response.content[0].text
        except APIError as exc:
            raise ProviderError(f"Anthropic API error: {exc}") from exc

    def list_models(self) -> List[str]:
        return self.DEFAULT_MODELS
