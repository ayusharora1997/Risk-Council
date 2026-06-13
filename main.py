"""
AI Risk Council — CLI entry point.

Run:
    python main.py

The wizard collects scenario, provider/model selections, scoring targets,
and then runs the full generate-review-improve loop with a live Rich dashboard.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Rich imports ──────────────────────────────────────────────────────────────
from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# ── dotenv — always load from the project directory, not CWD ─────────────────
try:
    from dotenv import load_dotenv
    _ENV_FILE = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=_ENV_FILE, override=False)
except ImportError:
    pass  # python-dotenv is optional; env vars can be set manually

# ── Project root on sys.path ──────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.generator_agent import GeneratorAgent
from agents.reviewer_agent import ReviewerAgent
from engine.iteration_engine import IterationEngine
from engine.scoring_engine import ScoringEngine
from exports.json_exporter import JSONExporter
from exports.markdown_exporter import MarkdownExporter
from models.schemas import ReviewerConfig, SessionConfig, SessionResult
from providers import AVAILABLE_PROVIDERS, get_provider
from providers.base_provider import ProviderError
from providers.ollama_provider import OllamaProvider
from storage.audit_trail import AuditTrail

# ---------------------------------------------------------------------------
# Console / theme setup
# ---------------------------------------------------------------------------

THEME = Theme({
    "info": "cyan",
    "success": "bold green",
    "warning": "yellow",
    "error": "bold red",
    "accent": "bold magenta",
    "muted": "dim white",
    "score_high": "bold green",
    "score_mid": "bold yellow",
    "score_low": "bold red",
})

console = Console(theme=THEME)

# ---------------------------------------------------------------------------
# Score colour helper
# ---------------------------------------------------------------------------

def _score_colour(score: float) -> str:
    if score >= 80:
        return "score_high"
    if score >= 60:
        return "score_mid"
    return "score_low"


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

def _print_banner() -> None:
    banner = Text(justify="center")
    banner.append("\n  AI RISK COUNCIL\n", style="bold magenta")
    banner.append("  Multi-Model Policy Governance Platform\n", style="cyan")
    banner.append("  Phase 1 MVP — Backend Engine\n", style="muted")
    console.print(Panel(banner, border_style="magenta", padding=(0, 4)))
    console.print()


# ---------------------------------------------------------------------------
# Provider / model selection helpers
# ---------------------------------------------------------------------------

def _check_provider_availability(provider_name: str) -> bool:
    """Return True if the required env var / service is present."""
    env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GOOGLE_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
    if provider_name in env_map:
        return bool(os.getenv(env_map[provider_name]))
    if provider_name == "ollama":
        try:
            p = OllamaProvider()
            return p.is_available()
        except Exception:
            return False
    return False


def _build_provider_table() -> Table:
    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan")
    table.add_column("#", justify="right", width=3)
    table.add_column("Provider", width=14)
    table.add_column("Status", width=12)
    table.add_column("Example Models")

    model_examples = {
        "openai": "gpt-4o, gpt-4o-mini",
        "anthropic": "claude-opus-4-8, claude-sonnet-4-6",
        "gemini": "gemini-2.0-flash, gemini-1.5-pro",
        "openrouter": "llama-3.3-70b, mistral-7b, deepseek-r1",
        "ollama": "llama3.2, mistral, gemma2 (local)",
    }
    for idx, name in enumerate(AVAILABLE_PROVIDERS, 1):
        available = _check_provider_availability(name)
        status = "[success]● Available[/]" if available else "[muted]○ Not configured[/]"
        table.add_row(str(idx), name.upper(), status, model_examples.get(name, ""))
    return table


def _select_provider_and_model(role: str) -> Tuple[str, str]:
    """Interactive provider + model selection. Returns (provider_name, model_id)."""
    console.print(f"\n[accent]Select {role} provider:[/]")
    console.print(_build_provider_table())

    while True:
        choice = Prompt.ask(
            f"  {role} provider",
            choices=AVAILABLE_PROVIDERS,
            default="openai",
        )
        try:
            provider = get_provider(choice)
            break
        except ProviderError as exc:
            console.print(f"  [error]Provider error: {exc}[/]")
            console.print("  [muted]Make sure the relevant API key is set in .env[/]")

    models = provider.list_models()
    console.print(f"\n  Available {choice.upper()} models:")
    for i, m in enumerate(models, 1):
        console.print(f"    [muted]{i}.[/] {m}")

    raw = Prompt.ask(f"  {role} model (name or number)", default=models[0])
    # Resolve a bare integer to the corresponding model name
    if raw.strip().isdigit():
        idx = int(raw.strip()) - 1
        if 0 <= idx < len(models):
            model = models[idx]
            console.print(f"  [muted]Resolved to: {model}[/]")
        else:
            console.print(f"  [warning]Index {raw} out of range — using default: {models[0]}[/]")
            model = models[0]
    else:
        model = raw.strip()
    return choice, model


def _select_reviewers() -> List[Dict[str, str]]:
    """Allow the user to add multiple reviewer slots."""
    reviewers: List[Dict[str, str]] = []
    console.print("\n[accent]Configure the Reviewer Council:[/]")
    console.print("[muted]Add one or more reviewer agents (different models = better coverage).[/]\n")

    while True:
        provider_name, model = _select_provider_and_model(
            f"Reviewer {len(reviewers) + 1}"
        )
        reviewers.append({"provider": provider_name, "model": model})
        console.print(f"  [success]Reviewer {len(reviewers)} added: {provider_name}/{model}[/]")

        if len(reviewers) >= 5:
            console.print("  [muted](Maximum 5 reviewers reached)[/]")
            break
        add_more = Confirm.ask("  Add another reviewer?", default=len(reviewers) < 2)
        if not add_more:
            break

    return reviewers


# ---------------------------------------------------------------------------
# Progress callback (called by IterationEngine after each phase)
# ---------------------------------------------------------------------------

_iteration_table: Optional[Table] = None
_all_rows: List[dict] = []


def _make_iteration_table() -> Table:
    t = Table(
        box=box.ROUNDED, show_header=True, header_style="bold cyan",
        title="[bold]Iteration Progress[/]", expand=True,
    )
    t.add_column("Iter", justify="right", width=5)
    t.add_column("Policy V", justify="right", width=8)
    t.add_column("Score", justify="right", width=8)
    t.add_column("Fairness", justify="right", width=9)
    t.add_column("Governance", justify="right", width=11)
    t.add_column("Controls", justify="right", width=10)
    t.add_column("Status", width=20)
    return t


def build_progress_callback(target_score: float) -> Any:
    """Return a closure that prints progress to the console."""

    def callback(payload: Dict[str, Any]) -> None:
        phase = payload.get("phase", "")

        if phase == "initial_generated":
            console.print("\n[success]Initial policy generated (Version 1)[/]")

        elif phase == "reviewing":
            n = payload.get("iteration", "?")
            v = payload.get("policy_version", "?")
            console.print(f"\n[info]Iteration {n}[/] — Reviewing policy V{v} with council...")

        elif phase == "iteration_complete":
            n = payload["iteration"]
            score = payload["score"]
            best = payload["best_score"]
            target = payload["target_score"]
            bd = payload.get("score_breakdown", {})
            duration = payload.get("duration_s", 0)
            reviewer_scores = payload.get("reviewer_scores", [])
            colour = _score_colour(score)

            console.print()
            console.print(Rule(f"[bold]Iteration {n} Complete[/]", style="cyan"))

            # ── Aggregate score panel ────────────────────────────────────
            score_text = Text()
            score_text.append(f"  Score:       ", style="bold")
            score_text.append(f"{score:.1f}/100\n", style=colour)
            score_text.append(f"  Best:        {best:.1f}/100\n")
            score_text.append(f"  Target:      {target:.1f}/100\n")
            score_text.append(f"  Duration:    {duration}s\n")
            if bd:
                score_text.append("\n  Breakdown (aggregated):\n", style="bold")
                for dim in ["fairness", "bias_mitigation", "ethical_soundness",
                            "governance", "controls", "practicality"]:
                    label = dim.replace("_", " ").title()
                    score_text.append(f"    {label:<25} {bd.get(dim, 0):.1f}\n")

            console.print(Panel(score_text, title=f"[bold]Iteration {n} — Aggregate Score[/]", border_style=colour))

            # ── Per-reviewer breakdown table ─────────────────────────────
            if reviewer_scores:
                rev_table = Table(
                    box=box.SIMPLE_HEAVY,
                    title="[bold]Per-Reviewer Scores[/]",
                    header_style="bold cyan",
                    show_lines=False,
                )
                rev_table.add_column("Reviewer", style="dim", min_width=28)
                rev_table.add_column("Fairness", justify="right", width=9)
                rev_table.add_column("Bias Mit.", justify="right", width=9)
                rev_table.add_column("Ethics", justify="right", width=8)
                rev_table.add_column("Govern.", justify="right", width=8)
                rev_table.add_column("Controls", justify="right", width=9)
                rev_table.add_column("Practical", justify="right", width=10)
                rev_table.add_column("TOTAL", justify="right", width=8, style="bold")

                for rs in reviewer_scores:
                    tc = _score_colour(rs["total"])
                    rev_table.add_row(
                        rs["reviewer"],
                        f"{rs['fairness']:.1f}",
                        f"{rs['bias_mitigation']:.1f}",
                        f"{rs['ethical_soundness']:.1f}",
                        f"{rs['governance']:.1f}",
                        f"{rs['controls']:.1f}",
                        f"{rs['practicality']:.1f}",
                        f"[{tc}]{rs['total']:.1f}[/]",
                    )
                console.print(rev_table)

        elif phase == "improving":
            n = payload.get("iteration", "?")
            nv = payload.get("new_version", "?")
            console.print(f"[info]Iteration {n}[/] — Generating improved policy V{nv}...")

        elif phase == "complete":
            reason = payload.get("termination_reason", "unknown")
            final = payload.get("final_score", 0)
            console.print()
            if reason == "target_reached":
                console.print(Panel(
                    f"[success]Target score achieved! Final score: {final:.1f}[/]",
                    title="[bold green]Session Complete[/]",
                    border_style="green",
                ))
            else:
                console.print(Panel(
                    f"[warning]Max iterations reached. Best score: {final:.1f}[/]",
                    title="[bold yellow]Session Complete[/]",
                    border_style="yellow",
                ))

    return callback


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def _offer_exports(result: SessionResult) -> None:
    console.print("\n[accent]Export Options:[/]")
    md_exp = MarkdownExporter()
    json_exp = JSONExporter()

    # ── Markdown ─────────────────────────────────────────────────────────────
    export_md_full = Confirm.ask(
        "  Export full Markdown report (all iterations + scores + feedback)?",
        default=True,
    )
    export_md_final = Confirm.ask(
        "  Export final policy only (clean standalone document)?",
        default=False,
    )
    export_md_versions = Confirm.ask(
        "  Export each policy version as a separate Markdown file?",
        default=False,
    )

    # ── JSON ──────────────────────────────────────────────────────────────────
    export_json = Confirm.ask("  Export full JSON data?", default=True)

    console.print()

    if export_md_full:
        path = md_exp.export(result)
        console.print(f"  [success]Full report:       [/] {path}")

    if export_md_final:
        path = md_exp.export_final_policy(result)
        console.print(f"  [success]Final policy only: [/] {path}")

    if export_md_versions:
        paths = md_exp.export_all_versions(result)
        for p in paths:
            console.print(f"  [success]Version file:     [/] {p}")

    if export_json:
        path = json_exp.export(result)
        console.print(f"  [success]JSON export:      [/] {path}")


# ---------------------------------------------------------------------------
# Final summary display
# ---------------------------------------------------------------------------

def _print_final_summary(result: SessionResult) -> None:
    scoring = ScoringEngine()
    console.print()
    console.print(Rule("[bold magenta]Session Summary[/]", style="magenta"))

    # Stats table
    stats = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    stats.add_column("Label", style="bold")
    stats.add_column("Value")

    stats.add_row("Session ID", result.session_id)
    stats.add_row("Termination", result.termination_reason.replace("_", " ").title())
    stats.add_row("Iterations Run", str(len(result.iterations)))
    stats.add_row("Final Score", f"{result.final_score:.1f}/100")
    stats.add_row("Best Score", f"{result.best_score:.1f}/100")
    stats.add_row("Target Score", f"{result.config.target_score:.1f}/100")
    stats.add_row("Total Duration", f"{result.total_duration_seconds:.0f}s")
    stats.add_row("Final Policy Length", f"{result.final_policy.word_count} words")
    console.print(stats)

    # Iteration score history
    if result.iterations:
        hist = Table(box=box.SIMPLE_HEAVY, title="Score History", header_style="cyan")
        hist.add_column("Iter", justify="right")
        hist.add_column("Policy V", justify="right")
        hist.add_column("Score", justify="right")
        hist.add_column("Δ Score", justify="right")

        prev_score = 0.0
        for rec in result.iterations:
            delta = rec.aggregated_score - prev_score
            delta_str = f"{delta:+.1f}" if prev_score else "--"
            delta_style = "green" if delta > 0 else ("red" if delta < 0 else "white")
            hist.add_row(
                str(rec.iteration_number),
                str(rec.policy_version),
                f"{rec.aggregated_score:.1f}",
                f"[{delta_style}]{delta_str}[/]",
            )
            prev_score = rec.aggregated_score
        console.print(hist)

    # Data location
    data_dir = Path("data") / "sessions" / result.session_id
    console.print(f"\n[muted]Audit trail stored at:[/] {data_dir.resolve()}")


# ---------------------------------------------------------------------------
# Main wizard
# ---------------------------------------------------------------------------

def main() -> None:
    _print_banner()

    # ── 1. Scenario input ───────────────────────────────────────────────────
    console.print(Rule("[bold cyan]Step 1 — Scenario[/]", style="cyan"))
    console.print("[muted]Describe the business scenario, process, SOP, or policy requirement.[/]")
    console.print("[muted]Be as specific as possible (press Enter when done).[/]\n")
    scenario = Prompt.ask("  Enter scenario").strip()
    if not scenario:
        console.print("[error]Scenario cannot be empty. Exiting.[/]")
        sys.exit(1)

    # ── 2. Generator model ──────────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold cyan]Step 2 — Generator Model[/]", style="cyan"))
    console.print("[muted]This model writes the initial policy and all subsequent improvements.[/]")
    gen_provider_name, gen_model = _select_provider_and_model("Generator")

    # ── 3. Reviewer models ──────────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold cyan]Step 3 — Reviewer Council[/]", style="cyan"))
    console.print("[muted]Each reviewer independently evaluates the policy and scores it.[/]")
    console.print("[muted]Using reviewers from different providers gives more balanced feedback.[/]")
    reviewer_raw = _select_reviewers()

    # ── 4. Scoring parameters ───────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold cyan]Step 4 — Scoring Parameters[/]", style="cyan"))

    target_score = FloatPrompt.ask(
        "  Target score (0-100) — stop when reached",
        default=85.0,
    )
    target_score = max(0.0, min(100.0, target_score))

    max_iterations = IntPrompt.ask(
        "  Maximum iterations",
        default=5,
    )
    max_iterations = max(1, min(20, max_iterations))

    # ── 5. Confirm configuration ────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold cyan]Step 5 — Confirm[/]", style="cyan"))

    confirm_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    confirm_table.add_column("Parameter", style="bold")
    confirm_table.add_column("Value")

    confirm_table.add_row("Scenario", scenario[:80] + ("..." if len(scenario) > 80 else ""))
    confirm_table.add_row("Generator", f"{gen_provider_name}/{gen_model}")
    for i, r in enumerate(reviewer_raw, 1):
        confirm_table.add_row(f"Reviewer {i}", f"{r['provider']}/{r['model']}")
    confirm_table.add_row("Target Score", f"{target_score:.1f}")
    confirm_table.add_row("Max Iterations", str(max_iterations))
    console.print(confirm_table)

    if not Confirm.ask("\n  Start the AI Risk Council?", default=True):
        console.print("[muted]Cancelled.[/]")
        sys.exit(0)

    # ── 6. Build components ─────────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold magenta]AI Risk Council Starting[/]", style="magenta"))

    try:
        gen_provider = get_provider(gen_provider_name)
    except ProviderError as exc:
        console.print(f"[error]Generator provider error: {exc}[/]")
        sys.exit(1)

    reviewer_configs: List[ReviewerConfig] = []
    reviewer_agents: List[ReviewerAgent] = []

    for r in reviewer_raw:
        try:
            rev_provider = get_provider(r["provider"])
            reviewer_agents.append(ReviewerAgent(provider=rev_provider, model=r["model"]))
            reviewer_configs.append(ReviewerConfig(provider=r["provider"], model=r["model"]))
        except ProviderError as exc:
            console.print(f"[warning]Skipping reviewer {r['provider']}/{r['model']}: {exc}[/]")

    if not reviewer_agents:
        console.print("[error]No valid reviewers configured. Exiting.[/]")
        sys.exit(1)

    session_config = SessionConfig(
        scenario=scenario,
        target_score=target_score,
        max_iterations=max_iterations,
        generator_provider=gen_provider_name,
        generator_model=gen_model,
        reviewer_configs=reviewer_configs,
    )

    generator = GeneratorAgent(provider=gen_provider, model=gen_model)
    audit = AuditTrail()
    audit.save_config(session_config)

    console.print(f"\n[muted]Session ID: [/][accent]{session_config.session_id}[/]")

    engine = IterationEngine(
        config=session_config,
        generator=generator,
        reviewers=reviewer_agents,
        audit=audit,
        progress_callback=build_progress_callback(target_score),
    )

    # ── 7. Run ──────────────────────────────────────────────────────────────
    try:
        result: SessionResult = engine.run()
    except KeyboardInterrupt:
        console.print("\n[warning]Interrupted by user. Partial results may be saved.[/]")
        sys.exit(0)
    except ProviderError as exc:
        console.print(f"\n[error]Provider error:[/] {exc}")
        console.print("[muted]Check your API key in .env and ensure the selected model exists.[/]")
        sys.exit(1)
    except Exception as exc:
        console.print(f"\n[error]Unexpected engine error:[/] {type(exc).__name__}: {exc}")
        console.print("[muted]Check the session data under data/sessions/ for partial results.[/]")
        sys.exit(1)

    # ── 8. Summary & export ──────────────────────────────────────────────────
    _print_final_summary(result)
    _offer_exports(result)

    console.print()
    console.print(Panel(
        "[success]AI Risk Council session complete.[/]",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
