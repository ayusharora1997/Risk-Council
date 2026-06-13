"""
OpenRouter provider — access to 200+ models (Llama, Mistral, DeepSeek, etc.)
via a single OpenAI-compatible API endpoint.
"""
from __future__ import annotations

import os
from typing import List, Optional

from openai import OpenAI, OpenAIError

from .base_provider import BaseProvider, ProviderError


class OpenRouterProvider(BaseProvider):
    provider_name = "openrouter"
    _BASE_URL = "https://openrouter.ai/api/v1"

    DEFAULT_MODELS: List[str] = [
        "meta-llama/llama-3.3-70b-instruct",
        "mistralai/mistral-7b-instruct",
        "deepseek/deepseek-r1",
        "google/gemma-2-9b-it:free",
        "microsoft/phi-3-mini-128k-instruct:free",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        site_url: Optional[str] = None,
        site_name: Optional[str] = None,
    ) -> None:
        key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise ProviderError(
                "OpenRouter API key missing. Set the OPENROUTER_API_KEY environment variable."
            )

        headers: dict = {}
        effective_url = site_url or os.getenv("OPENROUTER_SITE_URL", "")
        effective_name = site_name or os.getenv("OPENROUTER_SITE_NAME", "AI Risk Council")
        if effective_url:
            headers["HTTP-Referer"] = effective_url
        if effective_name:
            headers["X-Title"] = effective_name

        self.client = OpenAI(
            api_key=key,
            base_url=self._BASE_URL,
            default_headers=headers or None,
        )

    def generate(
        self,
        prompt: str,
        model: str = "meta-llama/llama-3.3-70b-instruct",
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
            raise ProviderError(f"OpenRouter API error: {exc}") from exc

    def list_models(self) -> List[str]:
        return self.DEFAULT_MODELS
