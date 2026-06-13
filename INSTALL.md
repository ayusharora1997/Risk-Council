# AI Risk Council — Installation & Usage Guide

## Requirements

- Python 3.12 or newer
- pip
- At least one AI provider API key (see Configuration)
- (Optional) Ollama installed locally for offline/local model support

---

## Quick Start

### 1. Clone / navigate to the project directory

```powershell
cd E:\Projects\Risk\ai_risk_council
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
# source .venv/bin/activate     # Mac / Linux
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

```powershell
copy .env.example .env
# Then edit .env and add your API keys
notepad .env
```

### 5. Run the application

```powershell
python main.py
```

---

## Configuration

| Variable | Required for | Where to get it |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI provider | platform.openai.com |
| `ANTHROPIC_API_KEY` | Anthropic provider | console.anthropic.com |
| `GOOGLE_API_KEY` | Gemini provider | aistudio.google.com |
| `OPENROUTER_API_KEY` | OpenRouter provider | openrouter.ai |
| `OLLAMA_BASE_URL` | Ollama (optional) | localhost:11434 default |

You only need to configure the providers you intend to use.

---

## Sample Execution Flow

```
AI RISK COUNCIL
Multi-Model Policy Governance Platform

──── Step 1 — Scenario ────────────────────────────────────
Describe the business scenario, process, SOP, or policy requirement.

  Enter scenario: We need an AI hiring algorithm policy for a global bank
                  covering fairness, bias prevention, and regulatory compliance.

──── Step 2 — Generator Model ──────────────────────────────
  Generator provider [openai/anthropic/gemini/openrouter/ollama]: anthropic
  Available models:
    1. claude-opus-4-8
    2. claude-sonnet-4-6
    3. claude-haiku-4-5-20251001
  Generator model: claude-opus-4-8

──── Step 3 — Reviewer Council ─────────────────────────────
  Reviewer 1 provider: openai
  Reviewer 1 model: gpt-4o
  Add another reviewer? [y/N]: y
  Reviewer 2 provider: gemini
  Reviewer 2 model: gemini-2.0-flash
  Add another reviewer? [y/N]: n

──── Step 4 — Scoring Parameters ───────────────────────────
  Target score (0-100): 85
  Maximum iterations: 5

──── Step 5 — Confirm ───────────────────────────────────────
  Generator:   anthropic/claude-opus-4-8
  Reviewer 1:  openai/gpt-4o
  Reviewer 2:  gemini/gemini-2.0-flash
  Target:      85.0
  Max iters:   5

  Start the AI Risk Council? [Y/n]: Y

Session ID: session_a3f2c1b9

Initial policy generated (Version 1)

Iteration 1 — Reviewing policy V1 with council...

┌─────────────────────────────────────┐
│ Iteration 1 Score                   │
│  Score:       72.4/100              │
│  Best:        72.4/100              │
│  Target:      85.0/100              │
│  Duration:    18s                   │
└─────────────────────────────────────┘

Iteration 1 — Generating improved policy V2...

Iteration 2 — Reviewing policy V2 with council...

┌─────────────────────────────────────┐
│ Iteration 2 Score                   │
│  Score:       86.1/100  ✓ TARGET    │
└─────────────────────────────────────┘

Session Complete — Target score achieved!

Score History:
  Iter 1:  72.4  (+0.0)
  Iter 2:  86.1  (+13.7)

Export Markdown report? [Y/n]: Y
  → data/exports/session_a3f2c1b9_report.md

Export JSON data? [Y/n]: Y
  → data/exports/session_a3f2c1b9_export.json
```

---

## Output Files

All outputs are written under the `data/` directory (created automatically):

```
data/
├── sessions/
│   └── session_<id>/
│       ├── config.json           # Session configuration
│       ├── iteration_001.json    # Iteration 1 full record
│       ├── iteration_002.json    # Iteration 2 full record
│       └── result.json           # Final consolidated result
└── exports/
    ├── session_<id>_report.md    # Human-readable Markdown report
    └── session_<id>_export.json  # Machine-readable JSON export
```

---

## Ollama (Local Models)

1. Install Ollama: https://ollama.com/download
2. Pull a model:
   ```powershell
   ollama pull llama3.2
   ollama pull mistral
   ```
3. Ollama will be listed as Available in the provider selection menu.

---

## Folder Structure

```
ai_risk_council/
├── agents/
│   ├── generator_agent.py   # Creates & improves policy documents
│   └── reviewer_agent.py    # Reviews policies, returns structured JSON
├── engine/
│   ├── iteration_engine.py  # Orchestrates the generate-review-improve loop
│   └── scoring_engine.py    # Weighted score aggregation
├── exports/
│   ├── markdown_exporter.py # Markdown report renderer
│   └── json_exporter.py     # JSON data export
├── models/
│   └── schemas.py           # All Pydantic data models
├── personas/
│   └── reviewer_personas.py # Phase 2: 10 specialist reviewer stubs
├── providers/
│   ├── base_provider.py     # Abstract provider interface
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   ├── gemini_provider.py
│   ├── openrouter_provider.py
│   └── ollama_provider.py
├── storage/
│   └── audit_trail.py       # JSON audit trail persistence
├── utils/
│   └── json_extractor.py    # Robust JSON extraction from LLM responses
├── data/                    # Auto-created at runtime
├── main.py                  # CLI entry point
├── requirements.txt
└── .env.example
```

---

## Phase 2 Roadmap

The following reviewer personas are stubbed in `personas/reviewer_personas.py`
and will be fully implemented in Phase 2:

1. **Risk Manager** — ISO 31000, COSO ERM alignment
2. **Internal Auditor** — IIA Standards, control testability
3. **Compliance Officer** — GDPR, AI Act, SOX, DORA mapping
4. **Cyber Security Expert** — NIST CSF, CIS Controls, ISO 27001
5. **Data Analyst** — Data quality, KPI definitions, analytics bias
6. **Process Excellence Expert** — Lean, Six Sigma, SIPOC
7. **Fraud Investigator** — ACFE Fraud Triangle, segregation of duties
8. **Business Continuity Specialist** — ISO 22301, RTO/RPO
9. **AI Governance Expert** — EU AI Act, NIST AI RMF
10. **Industry SME** — Sector-specific standards (PCI-DSS, HIPAA, MiFID II)

Future releases will also add:
- FastAPI / Flask REST layer
- Streamlit / React frontend
- Real-time WebSocket progress streaming
- Pandas-powered analytics dashboard
- Multi-session comparison reports
