#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Setting up Search Ads ML Demo"

# Backend
echo "==> Python backend"
cd "$ROOT/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r ../requirements.txt
python train_models.py

# Frontend
echo "==> React frontend"
cd "$ROOT/frontend"
npm install

echo ""
echo "Setup complete. Run: ./scripts/start.sh"
