#!/usr/bin/env bash
# AI Risk Council — Start both servers (macOS / Linux)
# Usage: bash start.sh

set -e

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Run 'bash setup.sh' first."
    exit 1
fi

if [ ! -f ".env" ]; then
    echo ".env not found. Copy .env.example to .env and add your API keys."
    exit 1
fi

echo ""
echo "Starting AI Risk Council..."
echo "  Backend  → http://localhost:8000"
echo "  Frontend → http://localhost:5173"
echo ""

# Start backend in background
.venv/bin/python run_api.py &
BACKEND_PID=$!
echo "Backend started (PID $BACKEND_PID)"

# Give backend a moment to bind
sleep 2

# Start frontend in background
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
echo "Frontend started (PID $FRONTEND_PID)"

echo ""
echo "Open http://localhost:5173 in your browser."
echo "Press Ctrl+C to stop both servers."
echo ""

# Wait and clean up on Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Servers stopped.'" INT TERM
wait
