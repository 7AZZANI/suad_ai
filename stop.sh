#!/usr/bin/env bash
# Stop the local stack started by ./start.sh
cd "$(dirname "$0")"
echo "Stopping admin UI…";  pkill -f "vite" 2>/dev/null || true
echo "Stopping backend…";   pkill -f "uvicorn app.main:app" 2>/dev/null || true
# Leave Ollama running by default (other apps may use it).
# Pass --all to also stop Ollama:
if [ "${1:-}" = "--all" ]; then
  echo "Stopping Ollama…"; pkill -f "ollama serve" 2>/dev/null || true
fi
echo "Done. (Ollama left running — use './stop.sh --all' to stop it too.)"
