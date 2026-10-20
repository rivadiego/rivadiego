from datetime import date

import pytest
from fastapi.testclient import TestClient

from coach_connect import coach
from coach_connect.api import create_app
from coach_connect.coach import CoachUnavailable, LLMClient, build_snapshot, offline_reply, render_context, reply
from coach_connect.config import Settings
from coach_connect.db import Database
from coach_connect.sources import DemoSource
from coach_connect.sync import Syncer

TODAY = date.today()


@pytest.fixture
def demo_db(tmp_path):
    db = Database(tmp_path / "coach.db")
    Syncer(DemoSource(), db, wellness_days=14).run()
    return db


def test_context_contains_plan_vitals_activities_and_loads(demo_db):
    text = render_context(build_snapshot(demo_db, Settings(athlete_name="Diego", athlete_height_cm=185), TODAY))

    assert "Atleta: Diego, 185 cm" in text
    assert "Scheda Hybrid Athlete" in text and "fase" in text
    assert "HRV notte" in text and "BALANCED" in text
    assert "Lungo domenicale" in text
    assert "Panca inclinata bilanciere" in text
    assert "Prossimi carichi calcolati" in text


def test_offline_coach_answers_loads_recovery_and_week(demo_db):
    snapshot = build_snapshot(demo_db, Settings(), TODAY)

    loads = offline_reply("Che carichi faccio oggi?", snapshot)
    recovery = offline_reply("Ho dormito male, sono stanco", snapshot)
    week = offline_reply("Com'è andata la settimana?", snapshot)

    assert "Workout" in loads and "×" in loads
    assert "Stanotte hai dormito" in recovery and "readiness" in recovery
    assert "sessioni su" in week and "km" in week
    assert all(coach.OFFLINE_NOTE in answer for answer in (loads, recovery, week))


def test_llm_receives_system_context_and_history(demo_db):
    settings = Settings(llm_api_key="sk-test", llm_model="test-model", llm_base_url="https://llm.example/v1")
    calls = []

    def fake_post(url, payload, headers, timeout):
        calls.append((url, payload, headers))
        return {"choices": [{"message": {"content": f"Risposta {len(calls)}"}}]}

    client = LLMClient(settings, post=fake_post)
    reply(demo_db, settings, "Ciao coach", today=TODAY, llm=client)
    messages = reply(demo_db, settings, "Che carichi oggi?", today=TODAY, llm=client)

    url, payload, headers = calls[-1]
    assert url == "https://llm.example/v1/chat/completions"
    assert headers["Authorization"] == "Bearer sk-test"
    assert payload["model"] == "test-model"
    assert payload["messages"][0]["role"] == "system" and "Prossimi carichi" in payload["messages"][0]["content"]
    assert [m["content"] for m in payload["messages"][1:]] == ["Ciao coach", "Risposta 1", "Che carichi oggi?"]
    assert messages[1]["content"] == "Risposta 2"


def test_llm_errors_become_coach_unavailable():
    def broken(*_):
        return {"unexpected": True}

    with pytest.raises(CoachUnavailable):
        LLMClient(Settings(llm_api_key="k", llm_model="m"), post=broken).complete([{"role": "user", "content": "x"}])


def test_chat_endpoints_offline(tmp_path):
    client = TestClient(create_app(Settings(db_path=tmp_path / "api.db", demo=True), DemoSource()))
    client.post("/api/sync")

    assert client.get("/api/chat").json() == {"messages": [], "coach_ai": False}
    sent = client.post("/api/chat", json={"content": "Che carichi faccio oggi?"}).json()
    assert [m["role"] for m in sent["messages"]] == ["user", "assistant"]
    assert len(client.get("/api/chat").json()["messages"]) == 2

    assert client.delete("/api/chat").status_code == 204
    assert client.get("/api/chat").json()["messages"] == []
    assert client.post("/api/chat", json={"content": ""}).status_code == 422
