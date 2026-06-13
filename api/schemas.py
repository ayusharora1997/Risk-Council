"""Request and response Pydantic models for the FastAPI layer."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Shared ────────────────────────────────────────────────────────────────────

class ModelConfig(BaseModel):
    provider: str
    model: str
    persona: Optional[str] = None


# ── Request models ────────────────────────────────────────────────────────────

class GeneratorGroupRequest(BaseModel):
    """One generator paired with its own reviewer council (1–3 reviewers)."""
    generator: ModelConfig
    reviewers: List[ModelConfig] = Field(min_length=1, max_length=3)


class SessionStartRequest(BaseModel):
    scenario: str = Field(min_length=10)
    document_type: str = Field(default="policy")   # "policy" | "sop" | "workflow"
    reference_content: Optional[str] = None         # pre-extracted text from uploaded file
    target_score: float = Field(ge=10, le=100, default=85.0)
    max_iterations: int = Field(ge=1, le=10, default=5)
    generator_groups: List[GeneratorGroupRequest] = Field(min_length=1, max_length=3)
    api_keys: Dict[str, str] = Field(default_factory=dict)


# ── Response models ───────────────────────────────────────────────────────────

class SessionResponse(BaseModel):
    session_id: str
    status: str   # "running" | "complete" | "error"


class ProviderInfo(BaseModel):
    name: str
    models: List[str]
    requires_key: bool


class ProvidersResponse(BaseModel):
    providers: List[ProviderInfo]
