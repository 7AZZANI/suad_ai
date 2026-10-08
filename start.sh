#!/usr/bin/env bash
# Start the whole local stack: Ollama + backend API + admin UI.
# Safe to re-run — it skips anything already running.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p data logs

# 1) Ollama daemon (local LLM)
if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "▶ starting Ollama…"
  nohup ollama serve > logs/ollama.log 2>&1 &
  for _ in $(seq 1 30); do
    curl -sf http://localhost:11434/api/tags >/dev/null 2>&1 && break
    sleep 1
  done
fi
echo "✓ Ollama up — models: $(curl -s http://localhost:11434/api/tags \
  | python3 -c 'import sys,json;print(", ".join(m["name"] for m in json.load(sys.stdin).get("models",[])))' 2>/dev/null || echo '?')"

# 2) Python venv + backend
if [ ! -d .venv ]; then
  python3 -m venv .venv
  ./.venv/bin/pip install -q -r requirements-core.txt
fi
if ! curl -sf http://localhost:8000/health >/dev/null 2>&1; then
  echo "▶ starting backend API…"
  ( cd backend && PYTHONPATH=. nohup ../.venv/bin/python -m uvicorn app.main:app \
      --host 127.0.0.1 --port 8000 > ../logs/backend.log 2>&1 & )
  for _ in $(seq 1 30); do
    curl -sf http://localhost:8000/health >/dev/null 2>&1 && break
    sleep 1
  done
fi
# Ensure default agent + roles exist (idempotent).
( cd backend && PYTHONPATH=. ../.venv/bin/python -m app.scripts.seed >/dev/null 2>&1 || true )
echo "✓ Backend up — http://localhost:8000  (API docs: /docs)"

# 3) Frontend admin UI
if [ ! -d frontend/node_modules ]; then
  ( cd frontend && npm install --silent )
fi
if ! curl -sf http://localhost:5173 >/dev/null 2>&1; then
  echo "▶ starting admin UI…"
  ( cd frontend && nohup npm run dev -- --host 127.0.0.1 --port 5173 \
      > ../logs/frontend.log 2>&1 & )
  for _ in $(seq 1 30); do
    curl -sf http://localhost:5173 >/dev/null 2>&1 && break
    sleep 1
  done
fi
echo "✓ Admin UI up"
echo
echo "──────────────────────────────────────────────"
echo "  Open:  http://localhost:5173"
echo "  API :  http://localhost:8000/docs"
echo "  Logs:  logs/{ollama,backend,frontend}.log"
echo "  Stop:  ./stop.sh"
echo "──────────────────────────────────────────────"
