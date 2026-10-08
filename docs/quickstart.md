# Quickstart — run fully local

Goal: a working AI agent on your machine with **no cloud accounts**.

## 1. Prerequisites

- Python 3.11+ (3.12 recommended)
- Node 18+ (for the admin UI)
- Optional: [Ollama](https://ollama.com) for real local LLM answers
- Optional: Docker (for the one-command full stack)

## 2. Backend

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-core.txt
cp .env.example .env
```

Edit `.env` and pick **one** database:

- **No Postgres (simplest):** comment out the Postgres `DATABASE_URL` line and
  uncomment the SQLite one:
  ```
  DATABASE_URL=sqlite+aiosqlite:///./data/suad.db
  ```
  Tables are auto-created on boot. Nothing else to do.
- **Postgres:** keep the default URL and run `make docker-up` (or your own
  Postgres), then `make migrate`.

Run it:

```bash
make dev
# API:  http://localhost:8000
# Docs: http://localhost:8000/docs
```

`GET /health` should return `{"status":"ok"}`.

## 3. Frontend

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
```

The Vite dev server proxies `/api`, `/health`, `/ready` to the backend, so no
extra config is needed.

## 4. Make it actually talk

The default LLM provider is **Ollama**. Install Ollama, then:

```bash
ollama pull qwen3:4b           # the default LLM_MODEL
ollama pull nomic-embed-text   # only needed for RAG/knowledge search
```

Open the UI → **Setup Wizard** → *Run all steps*:

| Check | Expected without extra setup |
|---|---|
| Database | ✅ (SQLite) or ✅ after `make docker-up` (Postgres) |
| LLM | ✅ if Ollama is running, ❌ otherwise (clear message) |
| STT | ✅ provider present (model loads on first use) |
| TTS | ✅ always (offline tone fallback if Piper absent) |
| Vector Memory | ✅ if Qdrant up, otherwise informational |
| Telephony | informational placeholder until credentials set |

## 5. Try it

- **Agent Playground** → ask *“What is the status of order 1001?”*
  (demo data returns *shipped via DHL*). This exercises the LLM → tool →
  permission → audit pipeline.
- **Voice Test** → upload a short `.wav`; you get transcript + reply + audio.
- **Permissions** → see the audit log fill up; try the appointment recipe to
  trigger an approval request.

## 6. Run the tests

```bash
make test     # 39 passing, fully offline
make lint     # clean
```

## Common setup issues

| Symptom | Fix |
|---|---|
| `Database is unavailable` | Use the SQLite `DATABASE_URL`, or `make docker-up`, or start Postgres. |
| LLM check fails | Start Ollama (`ollama serve`) and `ollama pull qwen3:4b`, or switch `LLM_PROVIDER` (see [providers.md](providers.md)). |
| `.env` value looks wrong (has a comment in it) | Keep comments on their **own line** — dotenv does not strip inline `# comments`. |
| Qdrant errors on search | RAG is optional; set `RAG_ENABLED=false` or start Qdrant (`make docker-up`). |
| Heavy `pip install` | Use `requirements-core.txt`; provider SDKs load lazily and only when used. |
| Frontend can't reach API | Ensure backend is on :8000, or set `VITE_API_BASE_URL` in `frontend/.env`. |
