import urllib.error
from datetime import date

import pytest
from fastapi.testclient import TestClient
from helpers import no_ollama, offline_coach

from coach_connect import coach
from coach_connect.api import create_app
from coach_connect.coach import (
    Coach,
    CoachUnavailable,
    LLMClient,
    OllamaClient,
    build_snapshot,
    offline_reply,
    render_context,
)
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


def fake_ollama(models, reply="Ciao! Oggi Workout B."):
    calls = []

    def get(url, timeout):
        calls.append(("GET", url, None))
        return {"models": [{"name": name} for name in models]}

    def post(url, payload, headers, timeout):
        calls.append(("POST", url, payload))
        return {"model": payload["model"], "message": {"role": "assistant", "content": reply}, "done": True}

    return get, post, calls


def test_context_contains_plan_vitals_activities_and_loads(demo_db):
    text = render_context(build_snapshot(demo_db, Settings(athlete_name="Diego", athlete_height_cm=185), TODAY))

    assert "Atleta: Diego, 185 cm" in text
    assert "Scheda Hybrid Athlete" in text and "Prossimo:" in text
    assert "Ultimi 7 giorni:" in text and "obiettivo 3 + 2" in text
    assert "HRV notte" in text and "BALANCED" in text
    assert "Lungo domenicale" in text
    assert "Panca inclinata bilanciere" in text
    assert "Prossimi carichi calcolati" in text
    assert "settimana 1" not in text.lower()


def test_offline_coach_answers_loads_recovery_and_week(demo_db):
    snapshot = build_snapshot(demo_db, Settings(), TODAY)

    loads = offline_reply("Che carichi faccio oggi?", snapshot)
    recovery = offline_reply("Ho dormito male, sono stanco", snapshot)
    week = offline_reply("Com'è andata la settimana?", snapshot)

    assert snapshot["plan"]["workouts"][snapshot["plan"]["next_workout"]]["title"] in loads and "×" in loads
    assert "Stanotte hai dormito" in recovery and "readiness" in recovery
    assert "Negli ultimi 7 giorni" in week and "km" in week
    assert all(coach.OFFLINE_NOTE in answer for answer in (loads, recovery, week))


def test_ollama_picks_an_installed_chat_model():
    get, post, _ = fake_ollama(["nomic-embed-text:latest", "llama3.2:3b", "qwen3:8b"])
    assert OllamaClient(Settings(), get=get, post=post).model == "qwen3:8b"

    get, post, _ = fake_ollama(["nomic-embed-text:latest"])
    assert OllamaClient(Settings(), get=get, post=post).model is None

    get, post, _ = fake_ollama(["gemma4:12b", "qwen3:8b"])
    assert OllamaClient(Settings(ollama_model="gemma4:12b"), get=get, post=post).model == "gemma4:12b"
    assert OllamaClient(Settings(ollama_model="qwen3:4b"), get=get, post=post).model is None

    assert OllamaClient(Settings(), get=no_ollama).model is None


def test_ollama_chat_request_and_thinking_removed():
    get, post, calls = fake_ollama(["qwen3:8b"], reply="<think>ragiono…</think>\nFai 3 serie.")
    client = OllamaClient(Settings(ollama_num_ctx=12000), get=get, post=post)

    answer = client.complete([{"role": "user", "content": "ciao"}])

    method, url, payload = calls[-1]
    assert (method, url) == ("POST", "http://localhost:11434/api/chat")
    assert payload["model"] == "qwen3:8b" and payload["stream"] is False and payload["think"] is False
    assert payload["options"] == {"num_ctx": 12000}
    assert answer == "Fai 3 serie."


def test_ollama_going_away_becomes_coach_unavailable():
    get, _, _ = fake_ollama(["qwen3:8b"])

    def refused(*_):
        raise urllib.error.URLError("connection refused")

    with pytest.raises(CoachUnavailable):
        OllamaClient(Settings(), get=get, post=refused).complete([{"role": "user", "content": "x"}])


def test_coach_prefers_api_key_then_ollama_then_offline():
    get, post, _ = fake_ollama(["qwen3:8b"])
    with_ollama = Coach(Settings(), ollama=OllamaClient(Settings(), get=get, post=post))
    with_key = Coach(Settings(llm_api_key="k", llm_model="m"), ollama=OllamaClient(Settings(), get=get, post=post))

    assert with_key.status() == {"mode": "api", "model": "m"}
    assert with_ollama.status() == {"mode": "ollama", "model": "qwen3:8b"}
    assert offline_coach(Settings()).status() == {"mode": "offline", "model": None}


def test_ollama_receives_system_context_and_history(demo_db):
    get, post, calls = fake_ollama(["qwen3:8b"])
    settings = Settings()
    trainer = Coach(settings, ollama=OllamaClient(settings, get=get, post=post))

    trainer.reply(demo_db, "Ciao coach", today=TODAY)
    messages = trainer.reply(demo_db, "Che carichi oggi?", today=TODAY)

    payload = calls[-1][2]
    assert payload["messages"][0]["role"] == "system" and "Prossimi carichi" in payload["messages"][0]["content"]
    assert [m["content"] for m in payload["messages"][1:]] == ["Ciao coach", "Ciao! Oggi Workout B.", "Che carichi oggi?"]
    assert messages[1]["content"] == "Ciao! Oggi Workout B."


def test_paid_api_request_format(demo_db):
    settings = Settings(llm_api_key="sk-test", llm_model="test-model", llm_base_url="https://llm.example/v1")
    calls = []

    def fake_post(url, payload, headers, timeout):
        calls.append((url, payload, headers))
        return {"choices": [{"message": {"content": "Risposta"}}]}

    trainer = Coach(settings, api=LLMClient(settings, post=fake_post), ollama=OllamaClient(settings, get=no_ollama))
    trainer.reply(demo_db, "Ciao", today=TODAY)

    url, payload, headers = calls[-1]
    assert url == "https://llm.example/v1/chat/completions"
    assert headers["Authorization"] == "Bearer sk-test" and payload["model"] == "test-model"


def test_chat_endpoints_offline(tmp_path):
    settings = Settings(db_path=tmp_path / "api.db", demo=True)
    client = TestClient(create_app(settings, DemoSource(), offline_coach(settings)))
    client.post("/api/sync")

    offline = {"mode": "offline", "model": None}
    assert client.get("/api/chat").json() == {"messages": [], "coach": offline}
    assert client.get("/api/status").json()["coach"] == offline
    sent = client.post("/api/chat", json={"content": "Che carichi faccio oggi?"}).json()
    assert [m["role"] for m in sent["messages"]] == ["user", "assistant"]
    assert len(client.get("/api/chat").json()["messages"]) == 2

    assert client.delete("/api/chat").status_code == 204
    assert client.get("/api/chat").json()["messages"] == []
    assert client.post("/api/chat", json={"content": ""}).status_code == 422
