# AI Risk Council

**Multi-Model AI Governance Platform** — generate enterprise policies, SOPs, and workflow designs, then run them through a configurable AI review council that scores, critiques, and iteratively improves every document.

> **Bring Your Own Keys.** AI Risk Council is BYOK — your API keys run directly against the providers and are never stored on any server.

---

## What it does

1. You describe a governance scenario (e.g. *"AI hiring policy for a global bank covering fairness, bias prevention, and GDPR"*).
2. You pick a document type: **Policy**, **SOP**, or **Workflow Design**.
3. Optionally upload an existing document (PDF, Word, Excel, CSV) as a reference.
4. Configure up to **3 generator groups**, each with its own **reviewer council** (up to 3 reviewers per group).
5. The engine iterates — **generate → review → score → improve** — until your target score is reached or iterations are exhausted.
6. Compare results across generator groups and download every draft, every review, and the final document in **Markdown or Word (.docx)**.

---

## Supported providers

| Provider | Models |
|---|---|
| **OpenAI** | gpt-4o, gpt-4o-mini, o1, o3-mini, … |
| **Anthropic** | claude-opus-4-8, claude-sonnet-4-6, claude-haiku-4-5, … |
| **Google Gemini** | gemini-2.0-flash, gemini-2.5-pro, … |
| **OpenRouter** | Any model via openrouter.ai |
| **Ollama** | Any locally-hosted model (no key required) |

---

## Prerequisites

| Tool | Minimum version | Install |
|---|---|---|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| npm | 9+ | bundled with Node.js |

At least one provider API key (or Ollama running locally).

---

## Quick start — Windows (PowerShell)

```powershell
# 1. Clone
git clone https://github.com/YOUR_USERNAME/ai-risk-council.git
cd ai-risk-council

# 2. Run setup (creates .venv, installs all dependencies, copies .env)
.\setup.ps1

# 3. Add your API keys
notepad .env

# 4. Start both servers (opens two terminal windows)
.\start.ps1
```

Then open **http://localhost:5173** in your browser.

---

## Quick start — macOS / Linux (bash)

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/ai-risk-council.git
cd ai-risk-council

# 2. Run setup
bash setup.sh

# 3. Add your API keys
nano .env   # or: code .env / vim .env

# 4. Start both servers
bash start.sh
```

Then open **http://localhost:5173** in your browser.

---

## Manual start (separate terminals)

If you prefer full control, run each server in its own terminal:

**Terminal 1 — Backend (FastAPI)**

```powershell
# Windows
.\.venv\Scripts\python.exe run_api.py
```

```bash
# macOS / Linux
.venv/bin/python run_api.py
```

The API is available at **http://localhost:8000**  
Interactive docs: **http://localhost:8000/docs**

**Terminal 2 — Frontend (React / Vite)**

```powershell
cd frontend
npm run dev
```

Open **http://localhost:5173**

---

## Environment variables

Copy `.env.example` to `.env` and fill in the keys you want to use:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
OPENROUTER_API_KEY=sk-or-...
OLLAMA_BASE_URL=http://localhost:11434   # default; only change if needed
```

You only need keys for the providers you actually use. Ollama requires no key.

---

## Using the REST API directly (PowerShell / curl)

The backend exposes a full REST + WebSocket API. You can drive it without the browser.

**Start a session**

```powershell
$body = @{
    scenario        = "AI hiring policy for a fintech covering fairness and GDPR"
    document_type   = "policy"
    target_score    = 85
    max_iterations  = 5
    generator_groups = @(
        @{
            generator = @{ provider = "openai"; model = "gpt-4o" }
            reviewers = @(
                @{ provider = "anthropic"; model = "claude-sonnet-4-6" }
            )
        }
    )
} | ConvertTo-Json -Depth 10

$resp = Invoke-RestMethod -Uri http://localhost:8000/api/sessions `
        -Method POST -ContentType "application/json" -Body $body

$sessionId = $resp.session_id
Write-Host "Session ID: $sessionId"
```

**Stream progress via WebSocket**

```powershell
# Use wscat (npm install -g wscat) or any WS client
wscat -c "ws://localhost:8000/api/sessions/$sessionId/ws"
```

**Poll for completion**

```powershell
do {
    $status = Invoke-RestMethod "http://localhost:8000/api/sessions/$sessionId"
    Write-Host "Status: $($status.status)"
    Start-Sleep 5
} while ($status.status -eq "running")
```

**Download exports**

```powershell
# Best-group final document as Word
Invoke-WebRequest "http://localhost:8000/api/sessions/$sessionId/export/group/0/final/docx" `
    -OutFile "final.docx"

# Specific iteration draft
Invoke-WebRequest "http://localhost:8000/api/sessions/$sessionId/export/group/0/iter/1/draft/docx" `
    -OutFile "iter1_draft.docx"

# Review council comments
Invoke-WebRequest "http://localhost:8000/api/sessions/$sessionId/export/group/0/iter/1/reviews/docx" `
    -OutFile "iter1_reviews.docx"

# Full Markdown report
Invoke-WebRequest "http://localhost:8000/api/sessions/$sessionId/export/markdown" `
    -OutFile "report.md"

# JSON data
Invoke-WebRequest "http://localhost:8000/api/sessions/$sessionId/export/json" `
    -OutFile "data.json"
```

Full API reference: **http://localhost:8000/docs**

---

## Project structure

```
ai-risk-council/
├── agents/
│   ├── generator_agent.py     # Creates & improves documents (Policy / SOP / Workflow)
│   └── reviewer_agent.py      # Reviews documents, returns structured scores
├── api/
│   ├── main.py                # FastAPI app entry point
│   ├── routers/
│   │   ├── sessions.py        # Session start, status, WebSocket
│   │   ├── exports.py         # Markdown, JSON, Word (.docx) downloads
│   │   └── attachments.py     # File upload & text extraction
│   ├── session_manager.py     # In-memory session registry
│   └── session_runner.py      # Multi-group async orchestration
├── engine/
│   ├── iteration_engine.py    # Generate → review → score → improve loop
│   └── scoring_engine.py      # Weighted 6-dimension score aggregation
├── exports/
│   ├── markdown_exporter.py   # Markdown report renderer
│   ├── json_exporter.py       # JSON data export
│   └── docx_exporter.py       # Word (.docx) export
├── frontend/                  # React + Vite + Tailwind CSS
│   └── src/
│       ├── pages/             # Landing, Configure, Session, Results, History
│       ├── components/        # ScoreGauge, IterationCard, PolicyViewer, …
│       ├── context/           # SessionContext (WebSocket state + localStorage history)
│       └── api/client.js      # API + WebSocket client
├── models/
│   └── schemas.py             # All Pydantic data models
├── providers/                 # OpenAI, Anthropic, Gemini, OpenRouter, Ollama adapters
├── storage/
│   └── audit_trail.py         # Per-session JSON audit trail
├── run_api.py                 # Start the FastAPI server
├── setup.ps1                  # Windows one-click setup
├── setup.sh                   # macOS/Linux one-click setup
├── start.ps1                  # Windows: start backend + frontend
├── start.sh                   # macOS/Linux: start backend + frontend
├── requirements.txt
└── .env.example               # API key template (copy to .env)
```

---

## Score dimensions

Every document is scored across six governance dimensions (0–100 each):

| Dimension | Weight | What it measures |
|---|---|---|
| Fairness | 15% | Non-discrimination, equitable treatment |
| Bias Mitigation | 15% | Specific controls to detect and reduce bias |
| Ethical Soundness | 15% | Alignment with ethical principles and human rights |
| Governance | 20% | Accountability, oversight, RACI clarity |
| Controls | 20% | Specific enforceable controls and audit mechanisms |
| Practicality | 15% | Implementability, resource feasibility |

---

## License

MIT — see [LICENSE](LICENSE).
