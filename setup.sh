#!/usr/bin/env bash
# AI Risk Council — macOS / Linux Setup Script
# Run once after cloning: bash setup.sh

set -e

echo ""
echo "================================================"
echo "  AI Risk Council — Setup"
echo "================================================"
echo ""

# 1. Python virtual environment
echo "[1/4] Creating Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "      .venv created."
else
    echo "      .venv already exists, skipping."
fi

# 2. Install Python dependencies
echo "[2/4] Installing Python dependencies..."
.venv/bin/pip install -r requirements.txt -q
echo "      Done."

# 3. Copy .env if missing
echo "[3/4] Checking environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "      .env created from .env.example"
    echo "      >>> Open .env and add your API keys before running. <<<"
else
    echo "      .env already exists, skipping."
fi

# 4. Frontend
echo "[4/4] Installing frontend dependencies (npm)..."
cd frontend && npm install --silent && cd ..
echo "      Done."

echo ""
echo "================================================"
echo "  Setup complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API keys"
echo "  2. Run bash start.sh  (or the two commands below in separate terminals)"
echo "       Backend:  .venv/bin/python run_api.py"
echo "       Frontend: cd frontend && npm run dev"
echo ""
