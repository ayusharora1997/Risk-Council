# AI Risk Council — Windows Setup Script
# Run this once after cloning the repo.
# Usage: .\setup.ps1

param(
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Risk Council — Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Python virtual environment ────────────────────────────
Write-Host "[ 1/4 ] Creating Python virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "        .venv created." -ForegroundColor Green
} else {
    Write-Host "        .venv already exists, skipping." -ForegroundColor DarkGray
}

# ── 2. Install Python dependencies ───────────────────────────
Write-Host "[ 2/4 ] Installing Python dependencies..." -ForegroundColor Yellow
& ".\.venv\Scripts\pip.exe" install -r requirements.txt --quiet
Write-Host "        Done." -ForegroundColor Green

# ── 3. Copy .env if missing ──────────────────────────────────
Write-Host "[ 3/4 ] Checking environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "        .env created from .env.example" -ForegroundColor Green
    Write-Host "        >>> Open .env and add your API keys before running. <<<" -ForegroundColor Magenta
} else {
    Write-Host "        .env already exists, skipping." -ForegroundColor DarkGray
}

# ── 4. Frontend dependencies ─────────────────────────────────
if (-not $SkipFrontend) {
    Write-Host "[ 4/4 ] Installing frontend dependencies (npm)..." -ForegroundColor Yellow
    Push-Location frontend
    npm install --silent
    Pop-Location
    Write-Host "        Done." -ForegroundColor Green
} else {
    Write-Host "[ 4/4 ] Skipping frontend (--SkipFrontend specified)." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Edit .env and add your API keys"
Write-Host "  2. Run .\start.ps1 to launch backend + frontend"
Write-Host "     OR run them separately:"
Write-Host "       Backend:  .\.venv\Scripts\python.exe run_api.py"
Write-Host "       Frontend: cd frontend && npm run dev"
Write-Host ""
