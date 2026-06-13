"""OpenAI provider — GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo, etc."""
from __future__ import annotations

import os
from typing import List, Optional

from openai import OpenAI, OpenAIError

from .base_provider import BaseProvider, ProviderError


class OpenAIProvider(BaseProvider):
    provider_name = "openai"

    DEFAULT_MODELS: List[str] = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
    ]

    def __init__(self, api_key: Optional[str] = None) -> None:
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ProviderError(
                "OpenAI API key missing. Set the OPENAI_API_KEY environment variable."
            )
        self.client = OpenAI(api_key=key)

    def generate(
        self,
        prompt: str,
        model: str = "gpt-4o",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except OpenAIError as exc:
            raise ProviderError(f"OpenAI API error: {exc}") from exc

    def list_models(self) -> List[str]:
        return self.DEFAULT_MODELS
