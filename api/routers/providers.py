"""GET /api/providers — returns all supported providers and their models."""
from __future__ import annotations

from fastapi import APIRouter

from api.schemas import ProviderInfo, ProvidersResponse
from providers import PROVIDER_DEFAULT_MODELS

router = APIRouter()

_REQUIRES_KEY = {"openai", "anthropic", "gemini", "openrouter"}


@router.get("", response_model=ProvidersResponse)
async def list_providers() -> ProvidersResponse:
    return ProvidersResponse(
        providers=[
            ProviderInfo(
                name=name,
                models=models,
                requires_key=name in _REQUIRES_KEY,
            )
            for name, models in PROVIDER_DEFAULT_MODELS.items()
        ]
    )
