"""End-to-end API smoke tests (no external services needed)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_ready_reports_db(client):
    body = client.get("/ready").json()
    assert body["database"] is True


def test_setup_summary(client):
    s = client.get("/api/setup/summary").json()
    assert s["llm"]["provider"] == "ollama"
    assert "***" not in s["llm"]["base_url"]  # base_url is not a secret


def test_tts_test_endpoint_works_offline(client):
    r = client.post("/api/setup/test-tts").json()
    assert r["ok"] is True  # tone fallback guarantees success


def test_tasks_listed(client):
    names = {t["name"] for t in client.get("/api/tasks").json()}
    assert "human_handoff" in names and "appointment_booking" in names


def test_tools_expose_risk_levels(client):
    tools = {t["name"]: t for t in client.get("/api/permissions/tools").json()}
    assert tools["book_appointment"]["risk_level"] == "approval"
    assert tools["get_current_time"]["risk_level"] == "safe"


def test_default_agent_autocreated(client):
    agents = client.get("/api/agents").json()
    assert any(a["name"] == "default" for a in agents)


def test_memory_search_degrades_gracefully(client):
    # RAG enabled but Qdrant not running -> graceful empty, not 500.
    r = client.post("/api/memory/search", json={"query": "hello"})
    assert r.status_code == 200
    assert r.json()["results"] == []
