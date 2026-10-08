# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-10-09

Initial public release.

### Added

- FastAPI backend with health/readiness endpoints and a permission-gated
  agent runtime (chat, voice, WebSocket).
- Pluggable providers behind factories + adapters, all configurable from `.env`:
  LLM (Ollama / OpenAI / OpenRouter / DashScope / Anthropic / vLLM / LM Studio),
  STT (faster-whisper), TTS (Piper / XTTS with offline tone fallback),
  telephony (LiveKit·SIP / Twilio), memory/RAG (Qdrant).
- Permission engine with `roles → scopes`, risk levels
  `safe / confirm / approval / blocked`, immutable `audit_logs`, and a human
  approval workflow.
- Tool registry with six built-in schema-described tools
  (`get_current_time`, `order_status_lookup`, `knowledge_search`,
  `create_support_ticket`, `book_appointment`, `human_handoff`).
- YAML task recipes (FAQ, order status, appointment booking, support ticket,
  human handoff).
- Admin UI in React + Vite: Setup Wizard, Provider Settings, Agent Playground,
  Voice Test, Task Recipes, Permissions, Connectors, Call Logs, System Status.
- Docker Compose stack (Postgres, Redis, Qdrant, API, UI) and one-command
  local stack (`start.sh` / `stop.sh`).
- Offline test suite (39 tests) — no external services required.