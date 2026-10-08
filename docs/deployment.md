# Deployment

## Docker Compose (recommended)

Brings up Postgres, Redis, Qdrant, the API and the admin UI:

```bash
cp .env.example .env          # keep the Postgres DATABASE_URL
make docker-up                # build + start (detached)
# UI:  http://localhost:5173
# API: http://localhost:8000/docs
make docker-down
```

`docker-compose.yml` overrides `DATABASE_URL`, `REDIS_URL`, `QDRANT_URL` to
the in-network service names, so your `.env` host values don't need editing.
The backend image installs `requirements-core.txt` for a small, reliable
build — switch the Dockerfile to `requirements.txt` if you need the full
provider stack (faster-whisper, livekit, etc.) inside the container.

## Database migrations

Local SQLite auto-creates tables on boot (dev convenience). **Postgres uses
Alembic:**

```bash
make migrate                              # alembic upgrade head
make makemigration m="add billing table"  # autogenerate after model changes
```

Alembic reads `DATABASE_URL` from settings (`backend/app/db/migrations/env.py`)
and runs async. The initial migration is `0001_initial`.

Seed default roles + a demo agent:

```bash
make seed
```

## Production checklist

- [ ] `APP_ENV=production`, strong `SECRET_KEY`.
- [ ] Real `DATABASE_URL` (managed Postgres) + run `make migrate`.
- [ ] `AUTO_APPROVE_RISKY_ACTIONS=false` (must stay false in prod).
- [ ] Replace `app/core/security.get_identity` with real auth (OIDC/JWT). The
      permission engine already consumes only an `Identity`.
- [ ] Lock `CORS_ORIGINS` to your real frontend origin(s).
- [ ] Put TLS + a reverse proxy (Caddy/Traefik/Nginx) in front of `:8000`.
- [ ] Persist volumes for Postgres and Qdrant; back them up.
- [ ] Set provider API keys via your secret manager, not a committed `.env`.
- [ ] Scale uvicorn workers behind the proxy; the app is stateless except DB.

## Running without Docker

```bash
pip install -r requirements.txt           # full stack
export $(grep -v '^#' .env | xargs)       # or use a process manager
cd backend && alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
# build the UI: cd frontend && npm run build  (serve dist/ via your proxy)
```

## Health & readiness

- `GET /health` — liveness, never touches dependencies (use for load balancer).
- `GET /ready` — readiness, reports DB connectivity without failing the
  request (`status: ok | degraded`).

## Observability

Structured single-line `key=value` logs go to stdout (`LOG_LEVEL` controls
verbosity) — ship them to your log pipeline. Every tool decision is also
persisted in `audit_logs` for security/compliance queries.
