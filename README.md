# AI Risk Council

> **Multi-Model AI Governance Platform** — generate enterprise Policies, SOPs, and Workflow Designs through a configurable multi-agent review council that scores, critiques, and iteratively improves every document.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776ab)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://react.dev)

**Bring Your Own Keys** — your API keys run directly against the providers and are never stored on any server.

---

## What it does

Describe a risk or governance scenario. The platform assembles a multi-agent council — independent AI generators and reviewers — that iterates through a structured loop until the document meets your quality target.

```
You describe the scenario
        │
        ▼
┌─────────────────────────────────────────────────┐
│              Generator Group 1                  │
│                                                 │
│  GeneratorAgent ──► draft ──► ReviewerAgent 1  │
│       ▲                  └──► ReviewerAgent 2  │
│       │                  └──► ReviewerAgent 3  │
│       │                            │           │
│       │                    ScoringEngine       │
│       │                     (aggregate)        │
│       │                            │           │
│       └──── improve(feedback) ◄────┘           │
│                  (repeat until target)         │
└─────────────────────────────────────────────────┘
        │
        ▼  (optional: Generator Group 2, Group 3)
        │
        ▼
 Best result selected ──► Export (.docx / .md / .json)
```

---

## Multi-Agent Architecture

This platform is built around a **multi-agent design pattern** where every actor — generators and reviewers — is an independent LLM call that can be powered by a *different model or provider*.

### Agents

| Agent | File | Role |
|---|---|---|
| **GeneratorAgent** | `agents/generator_agent.py` | Creates the initial document and produces improved versions based on aggregated council feedback. Has specialized system prompts for Policy, SOP, and Workflow document types. |
| **ReviewerAgent** | `agents/reviewer_agent.py` | Independently evaluates a document and returns a structured JSON score across six governance dimensions plus qualitative feedback: biases found, ethical risks, missing controls, and improvement recommendations. |

### Orchestration

| Component | File | Role |
|---|---|---|
| **IterationEngine** | `engine/iteration_engine.py` | Drives the `generate → review → score → improve` loop for one generator group. Runs all reviewer agents sequentially, aggregates their scores, checks termination conditions, and calls the generator to improve. |
| **ScoringEngine** | `engine/scoring_engine.py` | Aggregates scores from all reviewers using weighted averages across six dimensions. Builds a combined feedback dict passed to the generator for targeted improvement. |
| **SessionRunner** | `api/session_runner.py` | Runs up to 3 independent IterationEngine instances (one per generator group) and assembles the `MultiGroupResult`. Emits tagged WebSocket events (`group_index`, `groups_total`) so the frontend can track each group separately. |

### How a session flows

```
POST /api/sessions  →  session_id returned
WebSocket /api/sessions/{id}/ws  →  real-time event stream

Events emitted per group:
  group_start
  initial_generated          ← baseline draft ready
  reviewing (×N reviewers)   ← council evaluating
  iteration_complete         ← score + breakdown
  improving                  ← generator producing next version
  ... (repeat N iterations)
  group_complete

Final event:
  done  →  overall_best_score, overall_best_group_index
```

### Why multiple groups?

Running the same scenario through different generator models (e.g. GPT-4o vs Claude Opus vs Gemini) produces meaningfully different documents. Each group gets its own independent reviewer council. The platform compares all groups at the end and flags the winner — giving you a real, data-backed comparison rather than a single model's output.

### Score dimensions

| Dimension | Weight | What it measures |
|---|---|---|
| Fairness | 15 % | Non-discrimination, equitable treatment |
| Bias Mitigation | 15 % | Specific controls to detect and reduce bias |
| Ethical Soundness | 15 % | Alignment with ethical principles and human rights |
| Governance | 20 % | Accountability, oversight, RACI clarity |
| Controls | 20 % | Specific enforceable controls and audit mechanisms |
| Practicality | 15 % | Implementability, resource feasibility |

---

## Features

- **3 document types** — Policy, SOP, Workflow Design (each with a tailored AI prompt)
- **File attachments** — upload PDF, Word, Excel, or CSV as a reference; text is extracted server-side and injected into the generation context
- **Live session view** — WebSocket-streamed stage pipeline per group (Draft → Review → Improve)
- **Per-iteration Word exports** — download every draft and every set of review comments as `.docx`
- **Session history** — completed sessions auto-saved to `localStorage`; accessible from the History page
- **Full audit trail** — every iteration record persisted as JSON in `data/sessions/`
- **REST API** — full FastAPI backend with OpenAPI docs at `/docs`

---

## Supported providers

| Provider | Notes |
|---|---|
| **OpenAI** | gpt-4o, gpt-4o-mini, o3-mini, … |
| **Anthropic** | claude-opus-4-8, claude-sonnet-4-6, claude-haiku-4-5, … |
| **Google Gemini** | gemini-2.0-flash, gemini-2.5-pro, … |
| **OpenRouter** | Any model via openrouter.ai |
| **Ollama** | Any locally-hosted model — no API key required |

---

## Prerequisites

| Tool | Version |
|---|---|
| Python | 3.10 + |
| Node.js | 18 + |
| npm | 9 + |

---

## Quick start — Windows (PowerShell)

```powershell
git clone https://github.com/ayusharora1997/Risk-Council.git
cd Risk-Council

.\setup.ps1          # creates .venv, installs deps, copies .env

notepad .env         # add at least one provider API key

.\start.ps1          # opens backend + frontend in two terminal windows
```

Open **http://localhost:5173**

---

## Quick start — macOS / Linux

```bash
git clone https://github.com/ayusharora1997/Risk-Council.git
cd Risk-Council

bash setup.sh        # creates .venv, installs deps, copies .env

nano .env            # add at least one provider API key

bash start.sh        # starts backend + frontend
```

Open **http://localhost:5173**

---

## Manual start (two terminals)

**Terminal 1 — Backend**

```powershell
# Windows
.\.venv\Scripts\python.exe run_api.py
```
```bash
# macOS / Linux
.venv/bin/python run_api.py
```

API: **http://localhost:8000** · Docs: **http://localhost:8000/docs**

**Terminal 2 — Frontend**

```bash
cd frontend
npm run dev
```

---

## Using the API directly (PowerShell)

```powershell
# Start a session
$body = @{
    scenario        = "AI hiring policy for a fintech covering fairness and GDPR"
    document_type   = "policy"     # "policy" | "sop" | "workflow"
    target_score    = 85
    max_iterations  = 5
    generator_groups = @(
        @{
            generator = @{ provider = "openai"; model = "gpt-4o" }
            reviewers = @(
                @{ provider = "anthropic"; model = "claude-sonnet-4-6" }
                @{ provider = "gemini";    model = "gemini-2.0-flash" }
            )
        }
    )
} | ConvertTo-Json -Depth 10

$r = Invoke-RestMethod http://localhost:8000/api/sessions -Method POST `
     -ContentType "application/json" -Body $body

$id = $r.session_id

# Poll until complete
do {
    $s = Invoke-RestMethod "http://localhost:8000/api/sessions/$id"
    Write-Host "Status: $($s.status)"
    Start-Sleep 5
} while ($s.status -eq "running")

# Download exports
Invoke-WebRequest "http://localhost:8000/api/sessions/$id/export/group/0/final/docx"    -OutFile "final.docx"
Invoke-WebRequest "http://localhost:8000/api/sessions/$id/export/group/0/iter/1/draft/docx"   -OutFile "iter1_draft.docx"
Invoke-WebRequest "http://localhost:8000/api/sessions/$id/export/group/0/iter/1/reviews/docx" -OutFile "iter1_reviews.docx"
Invoke-WebRequest "http://localhost:8000/api/sessions/$id/export/markdown"             -OutFile "report.md"
```

---

## Environment variables

Copy `.env.example` → `.env` and fill in the keys you need:

| Variable | Provider | Where to get it |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI | platform.openai.com/api-keys |
| `ANTHROPIC_API_KEY` | Anthropic | console.anthropic.com |
| `GOOGLE_API_KEY` | Gemini | aistudio.google.com/app/apikey |
| `OPENROUTER_API_KEY` | OpenRouter | openrouter.ai/keys |
| `OLLAMA_BASE_URL` | Ollama | http://localhost:11434 (default) |

You only need keys for the providers you actually use.

---

## Project structure

```
ai-risk-council/
├── agents/
│   ├── generator_agent.py      # GeneratorAgent — creates & improves documents
│   └── reviewer_agent.py       # ReviewerAgent — scores & critiques each draft
├── engine/
│   ├── iteration_engine.py     # Orchestrates the generate→review→improve loop
│   └── scoring_engine.py       # Weighted 6-dimension score aggregation
├── api/
│   ├── main.py                 # FastAPI app
│   ├── session_runner.py       # Multi-group orchestration + WebSocket events
│   ├── session_manager.py      # In-memory session registry
│   └── routers/
│       ├── sessions.py         # Session start, status, WebSocket
│       ├── exports.py          # Markdown, JSON, Word (.docx) downloads
│       └── attachments.py      # File upload & text extraction
├── exports/
│   ├── docx_exporter.py        # Word (.docx) export — drafts, reviews, finals
│   ├── markdown_exporter.py    # Markdown report renderer
│   └── json_exporter.py        # JSON data export
├── frontend/                   # React 18 + Vite + Tailwind CSS
│   └── src/
│       ├── pages/              # Landing, Configure, Session, Results, History
│       ├── components/         # ScoreGauge, IterationCard, AppShell, …
│       └── context/            # SessionContext — WebSocket state + history
├── models/schemas.py           # All Pydantic data models
├── providers/                  # OpenAI, Anthropic, Gemini, OpenRouter, Ollama
├── storage/audit_trail.py      # Per-session JSON audit trail
├── run_api.py                  # Start the FastAPI dev server
├── setup.ps1 / setup.sh        # One-click setup (Windows / macOS+Linux)
├── start.ps1 / start.sh        # One-click start (Windows / macOS+Linux)
├── requirements.txt
└── .env.example                # API key template
```

---

## License

MIT — see [LICENSE](LICENSE).  
Copyright © 2026 Ayush Arora

---

**Repository:** [github.com/ayusharora1997/Risk-Council](https://github.com/ayusharora1997/Risk-Council)
