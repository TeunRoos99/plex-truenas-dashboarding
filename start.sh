#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# ---- virtualenv ----
if [ ! -d "$ROOT/.venv" ]; then
  echo "→ Virtualenv aanmaken..."
  python3 -m venv "$ROOT/.venv"
fi

source "$ROOT/.venv/bin/activate"

# ---- dependencies ----
echo "→ Dependencies installeren..."
pip install -q -r "$ROOT/requirements.txt"

# ---- .env check ----
if [ ! -f "$ROOT/.env" ]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo ""
  echo "⚠️  .env aangemaakt vanuit .env.example."
  echo "   Vul je TrueNAS en Plex gegevens in: $ROOT/.env"
  echo "   Daarna: ./start.sh"
  exit 1
fi

# ---- open frontend ----
echo "→ Frontend openen in browser..."
open "$ROOT/frontend/index.html" 2>/dev/null || true

# ---- backend starten ----
echo ""
echo "→ Backend starten op http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   Stop met Ctrl+C"
echo ""
cd "$ROOT/backend"
exec "$ROOT/.venv/bin/uvicorn" main:app --reload --port 8000
