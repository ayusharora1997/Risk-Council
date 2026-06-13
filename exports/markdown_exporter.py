"""
MarkdownExporter — renders a completed SessionResult into a single
human-readable Markdown report.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from models.schemas import IterationRecord, ReviewerFeedback, SessionResult

_EXPORT_ROOT = Path(__file__).resolve().parent.parent / "data" / "exports"


def _score_table(breakdown: dict) -> str:
    rows = [
        "| Dimension | Score | Weight |",
        "|-----------|------:|-------:|",
    ]
    weights = {
        "fairness": "15%", "bias_mitigation": "15%", "ethical_soundness": "15%",
        "governance": "20%", "controls": "20%", "practicality": "15%",
    }
    for dim, weight in weights.items():
        score = breakdown.get(dim, 0)
        rows.append(f"| {dim.replace('_', ' ').title()} | {score:.1f} | {weight} |")
    rows.append(f"| **TOTAL** | **{breakdown.get('total_score', 0):.1f}** | |")
    return "\n".join(rows)


def _reviewer_section(review: ReviewerFeedback, idx: int) -> str:
    lines = [
        f"#### Reviewer {idx}: `{review.reviewer_provider}/{review.reviewer_model}`",
        "",
        f"**Score:** {review.score.total_score:.1f}/100",
        "",
        _score_table(review.score.as_dict()),
        "",
    ]

    def _bullet_list(title: str, items: list) -> str:
        if not items:
            return f"**{title}:** *(none)*\n"
        return f"**{title}:**\n" + "\n".join(f"- {i}" for i in items) + "\n"

    lines += [
        _bullet_list("Biases Identified", review.biases),
        _bullet_list("Ethical Risks", review.ethical_risks),
        _bullet_list("Implementation Challenges", review.implementation_challenges),
        _bullet_list("Missing Controls", review.missing_controls),
        _bullet_list("Recommendations", review.recommendations),
        f"**Summary:** {review.summary}",
    ]
    return "\n".join(lines)


def _iteration_section(record: IterationRecord) -> str:
    lines = [
        f"## Iteration {record.iteration_number}",
        "",
        f"- **Timestamp:** {record.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"- **Policy Version:** {record.policy_version}",
        f"- **Aggregate Score:** {record.aggregated_score:.1f}/100",
        f"- **Generator:** `{record.generator_provider}/{record.generator_model}`",
        "",
    ]

    if record.score_breakdown:
        lines += ["### Score Breakdown", "", _score_table(record.score_breakdown), ""]

    lines += ["### Policy Document", "", "```markdown", record.policy_content, "```", ""]

    lines += ["### Individual Reviews", ""]
    for idx, review in enumerate(record.individual_reviews, 1):
        lines += [_reviewer_section(review, idx), ""]

    return "\n".join(lines)


class MarkdownExporter:
    """Exports a SessionResult to a Markdown report file."""

    def __init__(self, export_dir: Optional[Path] = None) -> None:
        self.export_dir = export_dir or _EXPORT_ROOT

    def export(self, result: SessionResult, filename: Optional[str] = None) -> Path:
        """Write the full session report (all iterations) and return the output path."""
        filename = filename or f"{result.session_id}_report.md"
        out_path = self.export_dir / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(self._render(result), encoding="utf-8")
        return out_path

    def export_final_policy(self, result: SessionResult, filename: Optional[str] = None) -> Path:
        """Export only the final (best) policy as a clean standalone document."""
        filename = filename or f"{result.session_id}_final_policy.md"
        out_path = self.export_dir / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)

        fp = result.final_policy
        lines = [
            f"# Governance Policy Document",
            f"> **Session:** `{result.session_id}`  ",
            f"> **Version:** {fp.version}  ",
            f"> **Score:** {result.best_score:.1f}/100  ",
            f"> **Generator:** `{fp.generator_provider}/{fp.generator_model}`  ",
            f"> **Generated:** {fp.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "---",
            "",
            fp.content,
            "",
            "---",
            f"*Produced by AI Risk Council — session `{result.session_id}`*",
        ]
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path

    def export_all_versions(self, result: SessionResult) -> List[Path]:
        """Export each policy version as a separate numbered Markdown file."""
        from pathlib import Path as _Path
        written: List[Path] = []
        seen_versions: set = set()

        for rec in result.iterations:
            v = rec.policy_version
            if v in seen_versions:
                continue
            seen_versions.add(v)

            filename = f"{result.session_id}_v{v:03d}.md"
            out_path = self.export_dir / filename
            out_path.parent.mkdir(parents=True, exist_ok=True)

            lines = [
                f"# Policy Version {v}",
                f"> **Session:** `{result.session_id}`  ",
                f"> **Iteration:** {rec.iteration_number}  ",
                f"> **Score at this iteration:** {rec.aggregated_score:.1f}/100  ",
                f"> **Generator:** `{rec.generator_provider}/{rec.generator_model}`",
                "",
                "---",
                "",
                rec.policy_content,
                "",
                "---",
                "",
                "## Reviewer Scores",
                "",
            ]
            for rv in rec.individual_reviews:
                lines += [
                    f"### {rv.reviewer_provider}/{rv.reviewer_model}",
                    f"**Total:** {rv.score.total_score:.1f}  |  "
                    f"Fairness: {rv.score.fairness:.1f}  |  "
                    f"Bias Mit.: {rv.score.bias_mitigation:.1f}  |  "
                    f"Ethics: {rv.score.ethical_soundness:.1f}  |  "
                    f"Governance: {rv.score.governance:.1f}  |  "
                    f"Controls: {rv.score.controls:.1f}  |  "
                    f"Practicality: {rv.score.practicality:.1f}",
                    "",
                    f"**Summary:** {rv.summary}",
                    "",
                ]
            out_path.write_text("\n".join(lines), encoding="utf-8")
            written.append(out_path)

        return written

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render(self, result: SessionResult) -> str:
        cfg = result.config
        blocks = [
            f"# AI Risk Council — Governance Report",
            "",
            f"> **Session:** `{result.session_id}`  ",
            f"> **Generated:** {result.completed_at.strftime('%Y-%m-%d %H:%M UTC')}  ",
            f"> **Termination:** {result.termination_reason.replace('_', ' ').title()}",
            "",
            "---",
            "",
            "## Session Configuration",
            "",
            f"| Parameter | Value |",
            f"|-----------|-------|",
            f"| Scenario | {cfg.scenario} |",
            f"| Generator | `{cfg.generator_provider}/{cfg.generator_model}` |",
            f"| Target Score | {cfg.target_score} |",
            f"| Max Iterations | {cfg.max_iterations} |",
            f"| Actual Iterations | {len(result.iterations)} |",
            f"| Final Score | **{result.final_score:.1f}** |",
            f"| Best Score | **{result.best_score:.1f}** |",
            f"| Duration | {result.total_duration_seconds:.0f}s |",
            "",
            "**Reviewer Council:**",
            "",
        ]

        for rc in cfg.reviewer_configs:
            persona = f" ({rc.persona})" if rc.persona else ""
            blocks.append(f"- `{rc.provider}/{rc.model}`{persona}")

        blocks += [
            "",
            "---",
            "",
            "## Final Policy Document",
            "",
            result.final_policy.content,
            "",
            "---",
            "",
            "## Iteration History",
            "",
        ]

        for record in result.iterations:
            blocks.append(_iteration_section(record))

        blocks += [
            "---",
            "",
            "## Initial Policy Document",
            "",
            result.initial_policy.content,
            "",
            "---",
            "",
            f"*Report generated by AI Risk Council — {result.completed_at.isoformat()}*",
        ]

        return "\n".join(blocks)
