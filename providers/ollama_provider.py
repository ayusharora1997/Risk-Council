"""
Ollama provider — locally-hosted open-source models via the Ollama REST API.
Requires Ollama running at http://localhost:11434 (or OLLAMA_BASE_URL).
"""
from __future__ import annotations

import os
from typing import List, Optional

import requests

from .base_provider import BaseProvider, ProviderError


class OllamaProvider(BaseProvider):
    provider_name = "ollama"

    DEFAULT_MODELS: List[str] = [
        "llama3.2",
        "mistral",
        "gemma2",
        "phi3",
        "qwen2.5",
    ]

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self._chat_url = f"{self.base_url}/api/chat"
        self._tags_url = f"{self.base_url}/api/tags"

    def generate(
        self,
        prompt: str,
        model: str = "llama3.2",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            response = requests.post(self._chat_url, json=payload, timeout=180)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except requests.RequestException as exc:
            raise ProviderError(
                f"Ollama request failed (is Ollama running at {self.base_url}?): {exc}"
            ) from exc
        except (KeyError, ValueError) as exc:
            raise ProviderError(f"Unexpected Ollama response format: {exc}") from exc

    def list_models(self) -> List[str]:
        """Return models currently pulled in the local Ollama instance."""
        try:
            response = requests.get(self._tags_url, timeout=5)
            response.raise_for_status()
            models = response.json().get("models", [])
            return [m["name"] for m in models] or self.DEFAULT_MODELS
        except Exception:
            return self.DEFAULT_MODELS

    def is_available(self) -> bool:
        """Quick liveness check — returns False if Ollama is not running."""
        try:
            return requests.get(self._tags_url, timeout=3).status_code == 200
        except Exception:
            return False
