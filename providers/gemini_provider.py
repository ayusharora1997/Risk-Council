"""Google Gemini provider — Gemini 2.0 Flash, 1.5 Pro, 1.5 Flash."""
from __future__ import annotations

import os
from typing import List, Optional

from .base_provider import BaseProvider, ProviderError


class GeminiProvider(BaseProvider):
    provider_name = "gemini"

    DEFAULT_MODELS: List[str] = [
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]

    def __init__(self, api_key: Optional[str] = None) -> None:
        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ProviderError(
                "Google API key missing. Set the GOOGLE_API_KEY environment variable."
            )
        try:
            import google.generativeai as genai

            genai.configure(api_key=key)
            self._genai = genai
        except ImportError as exc:
            raise ProviderError(
                "google-generativeai package not installed. Run: pip install google-generativeai"
            ) from exc

    def generate(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        # Gemini does not support a dedicated system role in all SDK versions;
        # prepend it to the prompt when provided.
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        try:
            gemini_model = self._genai.GenerativeModel(
                model_name=model,
                generation_config=self._genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            response = gemini_model.generate_content(full_prompt)
            return response.text
        except Exception as exc:
            raise ProviderError(f"Gemini API error: {exc}") from exc

    def list_models(self) -> List[str]:
        return self.DEFAULT_MODELS
