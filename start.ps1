# AI Risk Council — Start both servers (Windows)
# Usage: .\start.ps1

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    Write-Host "Virtual environment not found. Run .\setup.ps1 first." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path ".env")) {
    Write-Host ".env not found. Copy .env.example to .env and add your API keys." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting AI Risk Council..." -ForegroundColor Cyan
Write-Host "  Backend  → http://localhost:8000" -ForegroundColor DarkGray
Write-Host "  Frontend → http://localhost:5173" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop." -ForegroundColor DarkGray
Write-Host ""

# Launch backend in a new terminal window
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Write-Host 'Backend — http://localhost:8000' -ForegroundColor Cyan; `
     Set-Location '$PWD'; `
     .\.venv\Scripts\python.exe run_api.py"

# Give backend a moment to start, then launch frontend
Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Write-Host 'Frontend — http://localhost:5173' -ForegroundColor Cyan; `
     Set-Location '$PWD\frontend'; `
     npm run dev"

Write-Host "Both servers are starting in separate windows." -ForegroundColor Green
Write-Host "Open http://localhost:5173 in your browser." -ForegroundColor Green
Write-Host ""
