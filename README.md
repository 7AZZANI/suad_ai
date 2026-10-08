# Suad AI — Local-First AI Voice Agent Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-39%20passing-brightgreen.svg)](#tests)
[![Code style: ruff](https://img.shields.io/badge/style-ruff-261230.svg)](#make-targets)

A self-hosted **AI employee** for businesses. It can chat, listen, speak,
answer phone calls, use business tools, read a knowledge base, follow
permissions, and run predefined task playbooks.

**Local-first by default. Cloud optional via `.env`. No vendor is hardcoded.**

```
React + Vite admin UI  ──>  FastAPI backend  ──>  pluggable provider adapters
                                                   ├── LLM      (Ollama / OpenAI / OpenRouter / Claude / vLLM …)
                                                   ├── STT      (faster-whisper …)
                                                   ├── TTS      (Piper / XTTS …)
                                                   ├── Telephony(LiveKit·SIP / Twilio …)
                                                   └── Memory   (Qdrant, optional)
```

---

## Table of contents

- [60-second start](#60-second-start-zero-cloud-accounts-no-postgres)
- [Full stack with Docker](#full-stack-with-docker-postgres--redis--qdrant--api--ui)
- [One-command local stack](#one-command-local-stack-startshstopsh)
- [What's inside](#whats-inside)
- [Make targets](#make-targets)
- [Documentation](#documentation)
- [Project layout](#project-layout)
- [Tests](#tests)
- [Security model](#security-model-short-version)
- [Known limitations](#known-limitations)
- [Contributing](#contributing)
- [License](#license)

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

> The bundled Postgres/Redis credentials in `docker-compose.yml` are
> **dev-only defaults**. Change them before exposing anything beyond localhost.

## One-command local stack (`start.sh` / `stop.sh`)

```bash
./start.sh          # Ollama + backend (:8000) + frontend (:5173), idempotent
./stop.sh           # stops backend + UI, leaves Ollama running
./stop.sh --all     # stops everything
```

Logs are written to `logs/`. Prefer manual control? Run each piece yourself:

```bash
# Terminal 1
ollama serve

# Terminal 2
source .venv/bin/activate
make dev                                    # or: cd backend && python -m uvicorn app.main:app --port 8000

# Terminal 3
cd frontend && npm run dev
```

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
make install        core deps        make test         run tests
make install-full   all providers    make lint         ruff lint
make dev            run API          make format       ruff format/fix
make frontend       run admin UI     make migrate      alembic upgrade head
make docker-up       full stack       make makemigration m="..."   new migration
make docker-down     stop stack       make seed         seed roles + demo agent
make release v=1.2.3 release (bump + tag + push)
```

## Versioning & releases

The repo follows [Semantic Versioning](https://semver.org/) — `MAJOR.MINOR.PATCH`.
Backend and frontend are versioned as one unit (tag `vX.Y.Z`).

- **Fixes** → bump `PATCH` (0.1.0 → 0.1.1)
- **Features** → bump `MINOR`  (0.1.0 → 0.2.0)
- **Breaking changes** → bump `MAJOR` (0.1.0 → 1.0.0)

Cut a release in one command:

```bash
# 1. Update CHANGELOG.md first (move Unreleased -> new section)
make release v=0.1.1      # bumps version, commits, tags v0.1.1, pushes
```

Full policy and the manual/`--no-push` flow: [docs/releasing.md](docs/releasing.md).

## Documentation

| Guide | What it covers |
|---|---|
| [docs/quickstart.md](docs/quickstart.md) | Run fully local in minutes, troubleshooting table |
| [docs/configuration.md](docs/configuration.md) | Every `.env` setting, reference table |
| [docs/providers.md](docs/providers.md) | Swap providers, add a new adapter (3-step recipe) |
| [docs/local-llm.md](docs/local-llm.md) | Ollama with Qwen/Llama, vLLM, LM Studio |
| [docs/telephony.md](docs/telephony.md) | LiveKit/SIP vs Twilio, webhook simulation |
| [docs/tasks.md](docs/tasks.md) | Write task recipes & business tools |
| [docs/permissions.md](docs/permissions.md) | How the permission gate protects tools |
| [docs/deployment.md](docs/deployment.md) | Docker, Postgres, migrations, production checklist |
| [docs/releasing.md](docs/releasing.md) | Versioning & release workflow (`make release v=…`) |

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
docs/          quickstart, configuration, providers, local-llm, telephony, tasks, permissions, deployment
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

Read [docs/permissions.md](docs/permissions.md) for the full decision flow and
[docs/deployment.md](docs/deployment.md) for the production hardening checklist.

## Known limitations

Honest list of what is **not** production-ready yet — contributions welcome:

- **Auth is a dev shortcut.** Identity comes from optional `X-API-Key` /
  `X-Role` headers and is *not validated against a secret*. Replace with
  OIDC/JWT before any internet-facing deployment (see the production
  checklist in [docs/deployment.md](docs/deployment.md)).
- **No token streaming yet.** Chat replies are returned as a single JSON
  payload (including over WebSocket); SSE/streaming is on the roadmap.
- **Tool demos use in-memory data.** `app/tools/db_safe.py` ships demo
  orders/tickets/appointments — swap the handlers for real CRM/OMS calls.
- **Recipe `tools` lists are advisory.** Tool visibility is governed by each
  agent's `allowed_tools`; recipes contribute prompt steps.
- **Telephony webhooks are unsigned.** Twilio signature / LiveKit secret
  verification is not implemented yet.

Found something else? Please [open an issue](https://github.com/7AZZANI/suad_ai/issues).

## Contributing

Contributions are welcome — bug reports, docs, adapters, tests.

1. Fork and create a feature branch: `git checkout -b feat/my-change`
2. Install dev deps: `make install` (add `make install-full` for provider SDKs)
3. Make your change with tests where it makes sense
4. Run the gates: `make test && make lint`
5. Open a PR with a short description of *why* the change is needed

Guidelines:

- Keep the local-first principle: nothing may require a cloud account to boot.
- New providers go behind a factory + adapter — never hardcode a vendor in
  business logic (see [docs/providers.md](docs/providers.md)).
- Tools must declare a `scope` and `risk_level`; business data access goes
  through typed handlers, never LLM-generated SQL.
- Never commit `.env`, keys, or tokens — `.gitignore` blocks them, but review
  your diff before pushing anyway.

Please report security issues privately to the maintainer rather than a public
issue.

## License

MIT — see [LICENSE](LICENSE). You are free to use, modify, and distribute this
software, with the usual MIT notice retained.

---

Built to be understood by a new developer in under 30 minutes — start with
`backend/app/main.py` and follow the imports.
