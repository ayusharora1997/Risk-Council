"""
ScoringEngine — aggregates scores and feedback across multiple reviewers
into a single canonical result used by the iteration loop.
"""
from __future__ import annotations

from statistics import mean
from typing import Any, Dict, List

from models.schemas import ReviewerFeedback, SCORE_WEIGHTS


class ScoringEngine:
    """Aggregates multiple ReviewerFeedback objects into a weighted score."""

    WEIGHTS = SCORE_WEIGHTS
    DIMENSIONS = list(SCORE_WEIGHTS.keys())

    # ------------------------------------------------------------------
    # Score aggregation
    # ------------------------------------------------------------------

    def aggregate_score(self, reviews: List[ReviewerFeedback]) -> float:
        """Return the mean weighted total_score across all reviewers."""
        if not reviews:
            return 0.0
        return round(mean(r.score.total_score for r in reviews), 2)

    def aggregate_score_breakdown(self, reviews: List[ReviewerFeedback]) -> Dict[str, float]:
        """Return per-dimension averages plus the recomputed weighted total."""
        if not reviews:
            return {d: 0.0 for d in self.DIMENSIONS} | {"total_score": 0.0}

        breakdown: Dict[str, float] = {}
        for dim in self.DIMENSIONS:
            breakdown[dim] = round(mean(getattr(r.score, dim) for r in reviews), 2)

        breakdown["total_score"] = round(
            sum(breakdown[d] * self.WEIGHTS[d] for d in self.DIMENSIONS), 2
        )
        return breakdown

    # ------------------------------------------------------------------
    # Feedback aggregation
    # ------------------------------------------------------------------

    def aggregate_feedback(
        self, reviews: List[ReviewerFeedback], aggregate_score: float
    ) -> Dict[str, Any]:
        """Merge all reviewer feedback lists into deduplicated collections."""
        if not reviews:
            return {}

        def _merge(attr: str) -> List[str]:
            seen: set[str] = set()
            merged: List[str] = []
            for r in reviews:
                for item in getattr(r, attr, []):
                    normalised = item.strip()
                    if normalised and normalised not in seen:
                        seen.add(normalised)
                        merged.append(normalised)
            return merged

        return {
            "aggregate_score": aggregate_score,
            "biases": _merge("biases"),
            "ethical_risks": _merge("ethical_risks"),
            "implementation_challenges": _merge("implementation_challenges"),
            "missing_controls": _merge("missing_controls"),
            "recommendations": _merge("recommendations"),
            "summaries": [r.summary for r in reviews],
            "score_breakdown": self.aggregate_score_breakdown(reviews),
        }

    # ------------------------------------------------------------------
    # Scoring report
    # ------------------------------------------------------------------

    def score_report(self, reviews: List[ReviewerFeedback]) -> str:
        """Human-readable breakdown suitable for terminal output."""
        bd = self.aggregate_score_breakdown(reviews)
        lines = [
            f"  {'Dimension':<22} {'Score':>7}   {'Weight':>7}",
            "  " + "-" * 44,
        ]
        for dim in self.DIMENSIONS:
            weight_pct = f"{self.WEIGHTS[dim]*100:.0f}%"
            lines.append(f"  {dim.replace('_', ' ').title():<22} {bd[dim]:>7.1f}   {weight_pct:>7}")
        lines.append("  " + "-" * 44)
        lines.append(f"  {'TOTAL (weighted)':<22} {bd['total_score']:>7.1f}")
        return "\n".join(lines)
