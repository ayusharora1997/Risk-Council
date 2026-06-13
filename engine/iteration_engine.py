"""
IterationEngine — orchestrates the full generate → review → score → improve loop.

Flow per iteration:
  1. Review the current policy with all reviewer agents.
  2. Score and aggregate feedback.
  3. Record the iteration in the audit trail.
  4. Check termination conditions (target reached / max iterations).
  5. If continuing: ask the generator to produce an improved policy.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from agents.generator_agent import GeneratorAgent
from agents.reviewer_agent import ReviewerAgent
from engine.scoring_engine import ScoringEngine
from models.schemas import (
    IterationRecord,
    PolicyDocument,
    ReviewerConfig,
    SessionConfig,
    SessionResult,
)
from storage.audit_trail import AuditTrail

# Callback type: called after every iteration with a summary dict
ProgressCallback = Callable[[Dict[str, Any]], None]


class IterationEngine:
    """Drives the full multi-model policy refinement loop."""

    def __init__(
        self,
        config: SessionConfig,
        generator: GeneratorAgent,
        reviewers: List[ReviewerAgent],
        audit: AuditTrail,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> None:
        self.config = config
        self.generator = generator
        self.reviewers = reviewers
        self.audit = audit
        self.scoring = ScoringEngine()
        self.progress_callback = progress_callback

        self._iterations: List[IterationRecord] = []
        self._best_score: float = 0.0
        self._best_policy: Optional[PolicyDocument] = None

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self) -> SessionResult:
        """Execute the full generation-review-improvement loop and return the result."""
        session_start = time.time()
        termination_reason = "max_iterations_reached"

        # ── Step 0: Generate the initial policy ──────────────────────
        current_policy = self.generator.generate_initial(
            self.config.scenario,
            document_type=getattr(self.config, "document_type", "policy"),
            reference_content=getattr(self.config, "reference_content", None),
        )
        initial_policy = current_policy
        self._notify_progress({"phase": "initial_generated", "version": 1})

        # ── Iteration loop ────────────────────────────────────────────
        for iteration_number in range(1, self.config.max_iterations + 1):
            iter_start = time.time()

            # Step 1 — Review
            self._notify_progress({
                "phase": "reviewing",
                "iteration": iteration_number,
                "policy_version": current_policy.version,
            })
            reviews = self._run_reviews(current_policy)

            # Step 2 — Score
            aggregate_score = self.scoring.aggregate_score(reviews)
            score_breakdown = self.scoring.aggregate_score_breakdown(reviews)
            aggregated_feedback = self.scoring.aggregate_feedback(reviews, aggregate_score)

            # Step 3 — Record iteration
            record = IterationRecord(
                iteration_number=iteration_number,
                generator_model=self.config.generator_model,
                generator_provider=self.config.generator_provider,
                reviewer_configs=[
                    ReviewerConfig(provider=r.provider.provider_name, model=r.model, persona=r.persona)
                    for r in self.reviewers
                ],
                policy_version=current_policy.version,
                policy_content=current_policy.content,
                individual_reviews=reviews,
                aggregated_score=aggregate_score,
                score_breakdown=score_breakdown,
                aggregated_feedback=aggregated_feedback,
            )
            self._iterations.append(record)
            self.audit.save_iteration(self.config.session_id, record)

            # Track best
            if aggregate_score > self._best_score:
                self._best_score = aggregate_score
                self._best_policy = current_policy

            self._notify_progress({
                "phase": "iteration_complete",
                "iteration": iteration_number,
                "score": aggregate_score,
                "best_score": self._best_score,
                "target_score": self.config.target_score,
                "duration_s": round(time.time() - iter_start, 1),
                "score_breakdown": score_breakdown,
                "reviewer_scores": [
                    {
                        "reviewer": f"{r.reviewer_provider}/{r.reviewer_model}",
                        "total": r.score.total_score,
                        "fairness": r.score.fairness,
                        "bias_mitigation": r.score.bias_mitigation,
                        "ethical_soundness": r.score.ethical_soundness,
                        "governance": r.score.governance,
                        "controls": r.score.controls,
                        "practicality": r.score.practicality,
                    }
                    for r in reviews
                ],
            })

            # Step 4 — Termination check
            if aggregate_score >= self.config.target_score:
                termination_reason = "target_reached"
                break

            if iteration_number == self.config.max_iterations:
                break

            # Step 5 — Improve
            self._notify_progress({
                "phase": "improving",
                "iteration": iteration_number,
                "new_version": current_policy.version + 1,
            })
            current_policy = self.generator.improve(
                current_policy=current_policy,
                aggregated_feedback=aggregated_feedback,
                reviews=reviews,
                document_type=getattr(self.config, "document_type", "policy"),
            )

        # ── Build result ──────────────────────────────────────────────
        final_policy = self._best_policy or current_policy
        result = SessionResult(
            session_id=self.config.session_id,
            config=self.config,
            iterations=self._iterations,
            final_policy=final_policy,
            initial_policy=initial_policy,
            final_score=self._best_score,
            best_score=self._best_score,
            termination_reason=termination_reason,
            total_duration_seconds=round(time.time() - session_start, 1),
        )
        self.audit.save_session_result(result)
        self._notify_progress({
            "phase": "complete",
            "termination_reason": termination_reason,
            "final_score": self._best_score,
        })
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_reviews(self, policy: PolicyDocument) -> list:
        """Call every reviewer agent sequentially and return their feedback."""
        results = []
        for reviewer in self.reviewers:
            feedback = reviewer.review(policy)
            results.append(feedback)
        return results

    def _notify_progress(self, payload: Dict[str, Any]) -> None:
        if self.progress_callback:
            try:
                self.progress_callback(payload)
            except Exception:
                pass  # never let a callback crash the engine
