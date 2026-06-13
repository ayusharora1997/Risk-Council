"""
ReviewerAgent — critically evaluates a policy document and returns
structured JSON feedback with dimensional scores.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from models.schemas import PolicyDocument, ReviewerFeedback, ScoreBreakdown
from providers.base_provider import BaseProvider
from utils.json_extractor import extract_json, JSONExtractionError

_SYSTEM_PROMPT = """You are a critical expert on AI governance, risk management, and regulatory compliance.
Your role is to identify every weakness, gap, bias, and ethical concern in policy documents.
You must be rigorous, objective, and specific. Vague praise is not helpful.
A score of 90+ should only be awarded to a near-perfect, enterprise-ready document.
Always return ONLY a valid JSON object — no prose, no markdown outside the JSON block.
"""

_REVIEW_PROMPT_TEMPLATE = """Review the following policy document and return a structured JSON evaluation.

---BEGIN POLICY---
{policy_content}
---END POLICY---

Return ONLY this JSON structure (no surrounding text):

{{
  "score": {{
    "fairness": <integer 0-100>,
    "bias_mitigation": <integer 0-100>,
    "ethical_soundness": <integer 0-100>,
    "governance": <integer 0-100>,
    "controls": <integer 0-100>,
    "practicality": <integer 0-100>,
    "total_score": <weighted average — see weights below>
  }},
  "biases": ["<specific bias 1>", "..."],
  "ethical_risks": ["<specific ethical risk 1>", "..."],
  "implementation_challenges": ["<specific challenge 1>", "..."],
  "missing_controls": ["<specific missing control 1>", "..."],
  "recommendations": ["<actionable recommendation 1>", "..."],
  "summary": "<3-5 sentence overall assessment>"
}}

Scoring dimension weights for total_score computation:
  fairness:          15%
  bias_mitigation:   15%
  ethical_soundness: 15%
  governance:        20%
  controls:          20%
  practicality:      15%

Compute total_score = (fairness*0.15 + bias_mitigation*0.15 + ethical_soundness*0.15
                       + governance*0.20 + controls*0.20 + practicality*0.15)

Persona context (if applicable): {persona}

Be specific. List every issue you find. An empty list means no issues found.
"""


def _safe_float(value: Any, default: float = 50.0) -> float:
    """Coerce a value to float, falling back to default."""
    try:
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return default


def _parse_feedback(
    raw: Dict[str, Any],
    reviewer_model: str,
    reviewer_provider: str,
) -> ReviewerFeedback:
    """Convert the raw JSON dict into a validated ReviewerFeedback object."""
    score_raw = raw.get("score", {})

    fairness = _safe_float(score_raw.get("fairness", 50))
    bias_mit = _safe_float(score_raw.get("bias_mitigation", 50))
    ethical = _safe_float(score_raw.get("ethical_soundness", 50))
    governance = _safe_float(score_raw.get("governance", 50))
    controls = _safe_float(score_raw.get("controls", 50))
    practicality = _safe_float(score_raw.get("practicality", 50))

    # Trust the model's total if present; otherwise recompute
    if "total_score" in score_raw:
        total = _safe_float(score_raw["total_score"])
    else:
        total = round(
            fairness * 0.15
            + bias_mit * 0.15
            + ethical * 0.15
            + governance * 0.20
            + controls * 0.20
            + practicality * 0.15,
            2,
        )

    score = ScoreBreakdown(
        fairness=fairness,
        bias_mitigation=bias_mit,
        ethical_soundness=ethical,
        governance=governance,
        controls=controls,
        practicality=practicality,
        total_score=total,
    )

    def _str_list(key: str) -> List[str]:
        val = raw.get(key, [])
        if isinstance(val, list):
            return [str(v) for v in val if v]
        return []

    return ReviewerFeedback(
        score=score,
        biases=_str_list("biases"),
        ethical_risks=_str_list("ethical_risks"),
        implementation_challenges=_str_list("implementation_challenges"),
        missing_controls=_str_list("missing_controls"),
        recommendations=_str_list("recommendations"),
        summary=str(raw.get("summary", "No summary provided.")),
        reviewer_model=reviewer_model,
        reviewer_provider=reviewer_provider,
    )


class ReviewerAgent:
    """Reviews a policy document and returns structured dimensional feedback."""

    def __init__(
        self,
        provider: BaseProvider,
        model: str,
        persona: Optional[str] = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.persona = persona or "General GRC Expert"

    def review(self, policy: PolicyDocument) -> ReviewerFeedback:
        """Evaluate a policy document and return structured ReviewerFeedback.

        Falls back to a minimal feedback object with mid-range scores if the
        model returns unparseable output, so the iteration loop never crashes
        due to a single reviewer failure.
        """
        prompt = _REVIEW_PROMPT_TEMPLATE.format(
            policy_content=policy.content,
            persona=self.persona,
        )

        try:
            raw_response = self.provider.generate(
                prompt=prompt,
                model=self.model,
                system_prompt=_SYSTEM_PROMPT,
                temperature=0.3,  # low temperature for deterministic scoring
                max_tokens=2048,
            )
            raw_json = extract_json(raw_response)
            return _parse_feedback(raw_json, self.model, self.provider.provider_name)

        except JSONExtractionError as exc:
            # Return a fallback so the iteration engine can continue
            fallback_score = ScoreBreakdown(
                fairness=50, bias_mitigation=50, ethical_soundness=50,
                governance=50, controls=50, practicality=50,
                total_score=50,
            )
            return ReviewerFeedback(
                score=fallback_score,
                biases=[],
                ethical_risks=[],
                implementation_challenges=[],
                missing_controls=[f"Reviewer parse error: {exc}"],
                recommendations=["Re-run review — model returned non-JSON output."],
                summary=f"Review parse failed: {exc}",
                reviewer_model=self.model,
                reviewer_provider=self.provider.provider_name,
            )
