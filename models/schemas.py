"""
Pydantic schemas for every data structure in AI Risk Council.
All inter-module data flows through these typed models.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Scoring weight constants
# ---------------------------------------------------------------------------
SCORE_WEIGHTS: Dict[str, float] = {
    "fairness": 0.15,
    "bias_mitigation": 0.15,
    "ethical_soundness": 0.15,
    "governance": 0.20,
    "controls": 0.20,
    "practicality": 0.15,
}


class ProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


class DocumentType(str, Enum):
    POLICY = "policy"
    SOP = "sop"
    WORKFLOW = "workflow"


class ScoreBreakdown(BaseModel):
    """Six-dimension governance score returned by a reviewer."""

    fairness: float = Field(ge=0, le=100)
    bias_mitigation: float = Field(ge=0, le=100)
    ethical_soundness: float = Field(ge=0, le=100)
    governance: float = Field(ge=0, le=100)
    controls: float = Field(ge=0, le=100)
    practicality: float = Field(ge=0, le=100)
    total_score: float = Field(ge=0, le=100)

    def recompute_total(self) -> float:
        return round(
            self.fairness * SCORE_WEIGHTS["fairness"]
            + self.bias_mitigation * SCORE_WEIGHTS["bias_mitigation"]
            + self.ethical_soundness * SCORE_WEIGHTS["ethical_soundness"]
            + self.governance * SCORE_WEIGHTS["governance"]
            + self.controls * SCORE_WEIGHTS["controls"]
            + self.practicality * SCORE_WEIGHTS["practicality"],
            2,
        )

    def as_dict(self) -> Dict[str, float]:
        return {
            "fairness": self.fairness,
            "bias_mitigation": self.bias_mitigation,
            "ethical_soundness": self.ethical_soundness,
            "governance": self.governance,
            "controls": self.controls,
            "practicality": self.practicality,
            "total_score": self.total_score,
        }


class ReviewerFeedback(BaseModel):
    """Complete structured output from one reviewer agent pass."""

    score: ScoreBreakdown
    biases: List[str] = Field(default_factory=list)
    ethical_risks: List[str] = Field(default_factory=list)
    implementation_challenges: List[str] = Field(default_factory=list)
    missing_controls: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    summary: str
    reviewer_model: str
    reviewer_provider: str
    reviewed_at: datetime = Field(default_factory=datetime.utcnow)


class PolicyDocument(BaseModel):
    """A single versioned policy/SOP/workflow document produced by the GeneratorAgent."""

    version: int = 1
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    generator_model: str
    generator_provider: str

    @property
    def word_count(self) -> int:
        return len(self.content.split())

    @property
    def char_count(self) -> int:
        return len(self.content)


class ReviewerConfig(BaseModel):
    """Provider + model specification for one reviewer slot."""

    provider: str
    model: str
    persona: Optional[str] = None


class GeneratorGroupConfig(BaseModel):
    """One generator paired with its own reviewer council."""

    generator_provider: str
    generator_model: str
    reviewer_configs: List[ReviewerConfig]


class IterationRecord(BaseModel):
    """Full audit record for a single iteration cycle."""

    iteration_number: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    generator_model: str
    generator_provider: str
    reviewer_configs: List[ReviewerConfig]
    policy_version: int
    policy_content: str
    individual_reviews: List[ReviewerFeedback]
    aggregated_score: float
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    aggregated_feedback: Dict[str, Any] = Field(default_factory=dict)


class SessionConfig(BaseModel):
    """Configuration for one generator-group run (single generator + its reviewers)."""

    session_id: str = Field(default_factory=lambda: f"session_{uuid.uuid4().hex[:8]}")
    scenario: str
    document_type: str = "policy"          # "policy" | "sop" | "workflow"
    reference_content: Optional[str] = None  # extracted text from uploaded attachment
    target_score: float = Field(ge=0, le=100, default=85.0)
    max_iterations: int = Field(ge=1, le=20, default=5)
    generator_provider: str
    generator_model: str
    reviewer_configs: List[ReviewerConfig]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SessionResult(BaseModel):
    """Result for a single generator-group run."""

    session_id: str
    config: SessionConfig
    iterations: List[IterationRecord]
    final_policy: PolicyDocument
    initial_policy: PolicyDocument
    final_score: float
    best_score: float
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    termination_reason: str  # "target_reached" | "max_iterations_reached" | "error"
    total_duration_seconds: float = 0.0


class MultiGroupResult(BaseModel):
    """Top-level result encompassing all generator groups in a session."""

    session_id: str
    scenario: str
    document_type: str = "policy"
    reference_content: Optional[str] = None
    target_score: float
    max_iterations: int
    generator_groups: List[GeneratorGroupConfig]
    groups: List[SessionResult]          # one entry per generator group
    overall_best_score: float
    overall_best_group_index: int        # index into `groups`
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    total_duration_seconds: float = 0.0
