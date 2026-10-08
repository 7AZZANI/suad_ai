# Suad AI — Local-First AI Voice Agent Platform

A self-hosted **AI employee** for businesses. It can chat, listen, speak,
answer phone calls, use business tools, read a knowledge base, follow
permissions, and run predefined task playbooks.

**Local-first by default. Cloud optional via `.env`. No vendor is hardcoded.**

```
React + Vite admin UI  ──>  FastAPI backend  ──>  pluggable provider adapters
                                                   ├── LLM   (Ollama / OpenAI / OpenRouter / Claude / vLLM …)
                                                   ├── STT   (faster-whisper …)
                                                   ├── TTS   (Piper / XTTS …)
                                                   ├── Telephony (LiveKit·SIP / Twilio …)
                                                   └── Memory/RAG (Qdrant, optional)
```

---

## 60-second start (zero cloud accounts, no Postgres)

```bash
# 1. Backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-core.txt          # minimal, fast
cp .env.example .env
# In .env, switch DATABASE_URL to the SQLite line (commented in the file):
#   DATABASE_URL=sqlite+aiosqlite:///./data/suad.db
make dev                                       # http://localhost:8000/docs

# 2. Frontend (new terminal)
cd frontend && npm install && npm run dev      # http://localhost:5173
```

Open **http://localhost:5173** → *Setup Wizard* → *Run all steps*. Everything
except a live LLM/STT will be green out of the box (TTS uses an offline tone
fallback; RAG/telephony are optional placeholders).

To get real LLM answers locally, install [Ollama](https://ollama.com) and:

```bash
ollama pull qwen3:4b
ollama pull nomic-embed-text        # only if you want RAG
```

The defaults in `.env` already point at Ollama (`http://localhost:11434/v1`).

## Full stack with Docker (Postgres + Redis + Qdrant + API + UI)

```bash
cp .env.example .env
make docker-up      # http://localhost:5173  (API on :8000)
make docker-down
```

---

## To Run all at once in localhost = run this script on Terminal

./start.sh

& 

## Stop it script ready for it as well.

./stop.sh          # stops backend + UI, leaves Ollama running

& 

## Run it Manually

# Terminal 1
ollama serve

# Terminal 2
cd ~/Desktop/suad_ai && source .venv/bin/activate
cd backend && PYTHONPATH=. python -m uvicorn app.main:app --port 8000

# Terminal 3
cd ~/Desktop/suad_ai/frontend && npm run dev


---

## What's inside

| Area | Highlights |
|---|---|
| **Providers** | Swap LLM/STT/TTS/telephony/memory by editing `.env` — adapters, never hardcoded vendors. |
| **Agents** | Persona + allowed tools + RAG, provider-agnostic chat/tool loop. |
| **Permissions** | Roles → scopes; risk levels `safe / confirm / approval / blocked`; full audit log. |
| **Tools** | Schema-described, scope-gated. The LLM never runs SQL — only typed handlers do. |
| **Tasks** | YAML recipes: support tickets, appointments, order lookup, FAQ, human handoff. |
| **RAG** | Optional Qdrant ingestion + retrieval; degrades gracefully when disabled/offline. |
| **Telephony** | Normalized inbound-call interface; LiveKit/SIP (local) + Twilio (cloud) adapters. |
| **Admin UI** | Setup Wizard, Provider Settings, Playground, Voice Test, Recipes, Permissions, Connectors, Call Logs, Status. |

## Make targets

```
make install       core deps      make test        run tests
make install-full  all providers  make lint        ruff lint
make dev           run API        make format      ruff format/fix
make frontend      run admin UI   make migrate     alembic upgrade head
make docker-up     full stack     make seed        seed roles + demo agent
```

## Documentation

- [docs/quickstart.md](docs/quickstart.md) — run fully local in minutes
- [docs/configuration.md](docs/configuration.md) — every `.env` setting
- [docs/providers.md](docs/providers.md) — swap providers, add a new adapter
- [docs/local-llm.md](docs/local-llm.md) — Ollama with Qwen/Llama, vLLM, LM Studio
- [docs/telephony.md](docs/telephony.md) — LiveKit/SIP vs Twilio
- [docs/tasks.md](docs/tasks.md) — write task recipes & business tools
- [docs/permissions.md](docs/permissions.md) — how the gate protects tools
- [docs/deployment.md](docs/deployment.md) — Docker, Postgres, migrations, prod notes

## Project layout

```
backend/app/
  core/        config, logging, security, errors
  db/          session, models, alembic migrations
  providers/   llm/ stt/ tts/ telephony/ memory/  (base + adapters + factory)
  permissions/ roles, scopes, risk engine, audit
  tools/       registry, base, db_safe, builtin tools
  tasks/       YAML recipe loader + recipes/
  agents/      provider-agnostic runtime/orchestrator
  api/routes/  health, setup, agents, tasks, permissions, memory, telephony
  services/    agent + setup orchestration
frontend/src/  React + Vite + TS admin (pages/, components/, api.ts)
tests/         config, provider selection, permissions, tools, API
```

## Tests

```bash
make test       # 39 tests, no external services required
make lint       # ruff, clean
```

Tests that would need a live cloud provider are deliberately written against
the local fallbacks (tone TTS, `db=None` permission paths, fake LLM) so the
suite is fully green offline. See [docs/quickstart.md](docs/quickstart.md).

## Security model (short version)

1. Caller → `Identity(subject, role)` (header-based now; swap for OIDC later).
2. Every tool call → `PermissionEngine.evaluate()` → scope + risk decision.
3. `safe` runs; `confirm` needs `confirm=true`; `approval` creates a human
   approval record; `blocked` never runs.
4. Every decision is written to an immutable `audit_logs` row.
5. The LLM emits *tool requests*, never SQL. Handlers use parameterized,
   typed accessors only (`app/tools/db_safe.py`).

Built to be understood by a new developer in under 30 minutes — start with
`backend/app/main.py` and follow the imports.
