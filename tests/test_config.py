from app.core.config import Settings


def test_defaults_are_local_first():
    s = Settings()
    assert s.llm_provider == "ollama"
    assert s.stt_provider == "faster_whisper"
    assert s.tts_provider == "piper"
    assert s.telephony_provider == "livekit_sip"


def test_cors_origins_parsed_as_list():
    s = Settings(cors_origins="http://a.com, http://b.com")
    assert s.cors_origin_list == ["http://a.com", "http://b.com"]


def test_public_summary_scrubs_db_credentials():
    s = Settings(database_url="postgresql+asyncpg://user:secret@db:5432/x")
    summary = s.public_summary()
    assert "secret" not in summary["database"]
    assert "***" in summary["database"]


def test_relative_sqlite_path_is_made_absolute():
    s = Settings(database_url="sqlite+aiosqlite:///./data/test.db")
    assert s.database_url.startswith("sqlite+aiosqlite:////")
    assert "/data/test.db" in s.database_url
