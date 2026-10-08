# Configuration

All configuration is environment-driven via `.env` (loaded by
`backend/app/core/config.py`, a Pydantic `Settings` model). Unknown variables
are ignored; every variable has a safe local default.

> **Rule:** dotenv does **not** strip inline comments. Put comments on their
> own line, never after `KEY=value`.

## App

| Var | Default | Notes |
|---|---|---|
| `APP_NAME` | `Suad AI` | Shown in UI/health. |
| `APP_ENV` | `local` | `local` / `staging` / `production`. |
| `APP_HOST` / `APP_PORT` | `0.0.0.0` / `8000` | Bind address. |
| `LOG_LEVEL` | `INFO` | `DEBUG` for verbose tracing. |
| `SECRET_KEY` | dev string | Change in production (hashing salt). |
| `CORS_ORIGINS` | localhost:5173 | Comma-separated allowed origins. |

## LLM

| Var | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama`, `vllm`, `lmstudio`, `openrouter`, `openai`, `dashscope`, `anthropic`. |
| `LLM_BASE_URL` | Ollama URL | OpenAI-compatible base URL (ignored for `anthropic`). |
| `LLM_API_KEY` | `local` | Provider key; `local` for Ollama. |
| `LLM_MODEL` | `qwen3:4b` | Model id. |
| `LLM_TEMPERATURE` | `0.3` | Default sampling temperature. |
| `LLM_MAX_TOKENS` | `1024` | Default max output tokens. |
| `LLM_TIMEOUT_SECONDS` | `60` | Request timeout. |
| `ANTHROPIC_API_KEY` | _empty_ | Required only for `LLM_PROVIDER=anthropic`. |

## STT / TTS

| Var | Default | Notes |
|---|---|---|
| `STT_PROVIDER` | `faster_whisper` | or `null` to disable voice input. |
| `STT_MODEL` | `large-v3` | `tiny`…`large-v3`. |
| `STT_DEVICE` / `STT_COMPUTE_TYPE` | `auto` / `int8` | CPU/GPU + quantization. |
| `STT_LANGUAGE` | _empty_ | Blank = autodetect. |
| `TTS_PROVIDER` | `piper` | `piper`, `xtts`, `null`. |
| `TTS_VOICE` | _empty_ | Piper `.onnx` path; blank = offline tone fallback. |
| `TTS_PIPER_BINARY` | `piper` | Path/name of the Piper binary. |
| `XTTS_MODEL` | xtts_v2 | Coqui model id. |

## Telephony

| Var | Default | Notes |
|---|---|---|
| `TELEPHONY_PROVIDER` | `livekit_sip` | `livekit_sip`, `twilio`, `null`. |
| `LIVEKIT_URL` / `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` | _empty_ | LiveKit/SIP. |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_PHONE_NUMBER` | _empty_ | Twilio. |

## Memory / RAG (optional)

| Var | Default | Notes |
|---|---|---|
| `RAG_ENABLED` | `true` | `false` → agent skips retrieval entirely. |
| `MEMORY_PROVIDER` | `qdrant` | `qdrant` or `null`. |
| `QDRANT_URL` / `QDRANT_API_KEY` / `QDRANT_COLLECTION` | localhost | Vector store. |
| `EMBEDDING_BASE_URL` / `EMBEDDING_API_KEY` / `EMBEDDING_MODEL` / `EMBEDDING_DIM` | Ollama / `nomic-embed-text` / `768` | OpenAI-compatible embeddings endpoint. |

## Database & services

| Var | Default | Notes |
|---|---|---|
| `DATABASE_URL` | Postgres asyncpg | Use `sqlite+aiosqlite:///./data/suad.db` for zero-dependency local boot. Relative SQLite paths resolve against the repo root. |
| `REDIS_URL` | localhost:6379/0 | Reserved for future queue/cache use. |

## Permissions

| Var | Default | Notes |
|---|---|---|
| `DEFAULT_ROLE` | `operator` | Role for callers with no explicit identity. |
| `AUTO_APPROVE_RISKY_ACTIONS` | `false` | `true` auto-approves `approval`-tier actions — **dev only**. |

## How settings are consumed

`get_settings()` returns a cached singleton. Provider **factories** read it at
call time and are themselves `lru_cache`d, so changing `.env` requires a
backend restart. Tests clear these caches via the `patch_settings` fixture.
