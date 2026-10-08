"""Central configuration.

Every provider is selected and configured here via environment variables
(loaded from `.env`). There are NO hardcoded vendors anywhere else in the
codebase — adapters read their settings from this object only.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root = two levels above this file's package (backend/app/core -> repo).
REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPO_ROOT / ".env"


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Unknown env vars are ignored so a single `.env` can be shared across
    services without breaking validation.
    """

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- App ----
    app_name: str = "Suad AI"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production-please-32-chars-min"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ---- LLM ----
    llm_provider: str = "ollama"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "local"
    llm_model: str = "qwen3:4b"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1024
    llm_timeout_seconds: int = 60
    anthropic_api_key: str = ""

    # ---- STT ----
    stt_provider: str = "faster_whisper"
    stt_model: str = "large-v3"
    stt_device: str = "auto"
    stt_compute_type: str = "int8"
    stt_language: str = ""

    # ---- TTS ----
    tts_provider: str = "piper"
    tts_voice: str = ""
    tts_piper_binary: str = "piper"
    xtts_model: str = "tts_models/multilingual/multi-dataset/xtts_v2"

    # ---- Telephony ----
    telephony_provider: str = "livekit_sip"
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # ---- Memory / RAG ----
    rag_enabled: bool = True
    memory_provider: str = "qdrant"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "suad_knowledge"
    embedding_provider: str = "openai_compatible"
    embedding_base_url: str = "http://localhost:11434/v1"
    embedding_api_key: str = "local"
    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768

    # ---- Database & services ----
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/voice_agent"
    redis_url: str = "redis://localhost:6379/0"

    # ---- Permissions ----
    default_role: str = "operator"
    auto_approve_risky_actions: bool = False

    @model_validator(mode="after")
    def _normalize(self) -> Settings:
        # Resolve a relative SQLite path against the repo root so the DB file
        # location does not depend on the process working directory.
        url = self.database_url
        if url.startswith("sqlite") and ":///./" in url:
            rel = url.split(":///./", 1)[1]
            abs_path = (REPO_ROOT / rel).resolve()
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            self.database_url = url.split(":///./", 1)[0] + ":///" + str(abs_path)
        return self

    # ---- Derived helpers ----
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    def public_summary(self) -> dict[str, object]:
        """Non-secret view of the active configuration for the admin UI."""
        return {
            "app_env": self.app_env,
            "llm": {"provider": self.llm_provider, "model": self.llm_model,
                    "base_url": self.llm_base_url},
            "stt": {"provider": self.stt_provider, "model": self.stt_model},
            "tts": {"provider": self.tts_provider, "voice": self.tts_voice or "(default)"},
            "telephony": {"provider": self.telephony_provider},
            "rag": {"enabled": self.rag_enabled, "provider": self.memory_provider},
            "database": _scrub_dsn(self.database_url),
        }


def _scrub_dsn(dsn: str) -> str:
    """Hide credentials in a connection string for safe display."""
    if "@" not in dsn:
        return dsn
    scheme, rest = dsn.split("://", 1)
    _, host = rest.split("@", 1)
    return f"{scheme}://***@{host}"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton. Patch via `get_settings.cache_clear()` in tests."""
    return Settings()


settings = get_settings()
