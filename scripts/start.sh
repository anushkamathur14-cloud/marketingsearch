#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT

echo "==> Starting backend on http://localhost:8000"
cd "$ROOT/backend"
source .venv/bin/activate
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

echo "==> Starting frontend on http://localhost:5173"
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Dashboard: http://localhost:5173"
echo "API docs:  http://localhost:8000/docs"
echo "Press Ctrl+C to stop both servers."

wait
