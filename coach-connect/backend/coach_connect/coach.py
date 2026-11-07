"""The personal trainer chat: context built from the plan, the log and the vital signs."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from typing import Any

from .config import Settings
from .db import Database
from .plan import RULES, WEEKDAYS, WEEKLY_TARGET
from .planner import plan_payload
from .sources import SourceError
from .wellness import wellness_rows
from .workouts import done_by_day, feed, workouts_since

MONTHS = ("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre",
          "novembre", "dicembre")
OFFLINE_NOTE = (
    "*Coach offline: rispondo con regole automatiche sui tuoi dati. Per il coach AI gratuito collega GitHub Models "
    "al sito online, oppure installa Ollama sul computer del backend (vedi README).*"
)
# Families that chat well in Italian, tried in this order when OLLAMA_MODEL isn't set.
PREFERRED_OLLAMA_MODELS = ("qwen3", "qwen", "gemma", "llama", "mistral", "phi")


class CoachUnavailable(SourceError):
    status_code = 502
    code = "coach_unavailable"


def _kg(value: float | None) -> str:
    return "–" if value is None else f"{value:g}".replace(".", ",")


def _duration(seconds: float | None) -> str:
    if not seconds:
        return "–"
    minutes = round(seconds / 60)
    return f"{minutes // 60}h{minutes % 60:02d}" if minutes >= 60 else f"{minutes}'"


def _pace(speed: float | None) -> str:
    if not speed:
        return ""
    total = round(1000 / speed)
    return f" ({total // 60}:{total % 60:02d}/km)"


def _set_text(s: dict[str, Any], measure: str = "reps") -> str:
    if measure == "seconds":
        return f"{s.get('seconds') or '–'}\""
    if s.get("note"):
        return f"{s['note']}×{s.get('reps') or '–'}"
    if s.get("weight_kg") in (None, 0):
        return f"{s.get('reps') or '–'} rip"
    return f"{_kg(s['weight_kg'])}×{s.get('reps') or '–'}"


def _short_date(iso: str) -> str:
    day = date.fromisoformat(iso[:10])
    return f"{WEEKDAYS[day.weekday()].lower()} {day.day}/{day.month}"


def build_snapshot(db: Database, settings: Settings, today: date) -> dict[str, Any]:
    since = (today - timedelta(days=13)).isoformat()
    last_week = done_by_day(db, today - timedelta(days=6), today)
    return {
        "today": today,
        "athlete": {"name": settings.athlete_name, "height_cm": settings.athlete_height_cm},
        "plan": plan_payload(db, settings, today),
        "week": {
            "gym": sum(1 for d in last_week.values() if d["gym"]),
            "run": sum(1 for d in last_week.values() if d["run"]),
        },
        "wellness": wellness_rows(db, today=today, days=settings.wellness_days),
        "activities": [a for a in feed(db, limit=60, since_local=since) if a["source"] == "garmin"],
        "workouts": workouts_since(db, since),
    }


def _next_line(plan: dict[str, Any]) -> str:
    nxt = plan["workouts"][plan["next_workout"]]["title"]
    last = plan["last_workout"]
    if last is None:
        return f"Prossimo allenamento in palestra: {nxt} (nessun allenamento registrato finora)."
    when = "oggi" if plan["done_today"] else _short_date(last["date"])
    return f"Ultimo allenamento in palestra: {last['title']} ({when}). Prossimo: {nxt}."


def render_context(snapshot: dict[str, Any]) -> str:
    today: date = snapshot["today"]
    plan = snapshot["plan"]
    athlete = snapshot["athlete"]
    week = snapshot["week"]
    lines = [
        f"Oggi è {WEEKDAYS[today.weekday()].lower()} {today.day} {MONTHS[today.month - 1]} {today.year}.",
        f"Programma: {plan['name']} ({plan['subtitle']}), con 2 corse a settimana (una di qualità e un lungo).",
        _next_line(plan),
        f"Ultimi 7 giorni: {week['gym']} sessioni di palestra e {week['run']} corse "
        f"(obiettivo {WEEKLY_TARGET['gym']} + {WEEKLY_TARGET['run']}).",
    ]
    profile = [part for part in (
        athlete.get("name"),
        f"{athlete['height_cm']:g} cm" if athlete.get("height_cm") else None,
        f"{_kg(plan['bodyweight_kg'])} kg" if plan.get("bodyweight_kg") else None,
    ) if part]
    if profile:
        lines.append("Atleta: " + ", ".join(profile) + ".")

    lines += ["", "Parametri vitali (Garmin), dal più recente:",
              "data | sonno (punteggio) | HRV notte, stato | FC riposo | Body Battery risveglio/min | stress | passi | readiness"]
    for w in snapshot["wellness"]:
        lines.append(" | ".join([
            w["date"][5:],
            f"{_duration(w['sleep_seconds'])} ({_kg(w['sleep_score'])})",
            f"{_kg(w['hrv_last_night_ms'])} ms {w['hrv_status'] or ''}".strip(),
            _kg(w["resting_hr"]),
            f"{_kg(w['body_battery_wake'] or w['body_battery_high'])}/{_kg(w['body_battery_low'])}",
            _kg(w["stress_avg"]),
            _kg(w["steps"]),
            f"{_kg(w['readiness_score'])} {w['readiness_level'] or ''}".strip(),
        ]))
    if not snapshot["wellness"]:
        lines.append("(nessun dato disponibile)")

    lines += ["", "Attività Garmin ultimi 14 giorni:"]
    for a in snapshot["activities"]:
        distance = f" {a['distance_m'] / 1000:.1f} km".replace(".", ",") if a["distance_m"] else ""
        hr = f", FC media {round(a['avg_hr'])}" if a["avg_hr"] else ""
        lines.append(f"- {a['start_time_local'][5:16]} {a['name']}:{distance} in {_duration(a['duration_s'])}"
                     f"{_pace(a['avg_speed_mps']) if a['sport'] == 'run' else ''}{hr}")
    if not snapshot["activities"]:
        lines.append("(nessuna)")

    lines += ["", "Allenamenti di palestra registrati ultimi 14 giorni:"]
    for w in snapshot["workouts"]:
        exercises = "; ".join(
            f"{e['name']} " + ", ".join(_set_text(s, e["measure"]) for s in e["sets"]) for e in w["exercises"]
        )
        hr = f" (FC media {round(w['avg_hr'])})" if w.get("avg_hr") else ""
        lines.append(f"- {w['start_time_local'][5:16]} {w['name']}{hr}: {exercises}")
    if not snapshot["workouts"]:
        lines.append("(nessuno)")

    lines += ["", "Prossimi carichi calcolati dalle regole della scheda (usali, non ricalcolarli):"]
    for workout in plan["workouts"].values():
        parts = []
        for e in workout["exercises"]:
            sets = ", ".join(_set_text(s) for s in e["suggestion"]["sets"])
            parts.append(f"{e['name']} {sets} — {e['suggestion']['message']}")
        lines.append(f"{workout['title']}: " + " | ".join(parts))
    return "\n".join(lines)


def system_prompt(snapshot: dict[str, Any]) -> str:
    rules = "\n".join(f"- {r['title']}: {r['text']}" for r in RULES)
    name = snapshot["athlete"].get("name")
    athlete = f"{name}, un atleta ibrido" if name else "un atleta ibrido"
    return (
        f"Sei il personal trainer di {athlete} (palestra upper body + corsa). Parli in italiano, "
        "in modo diretto, pratico e motivante, con risposte brevi (massimo 8-10 righe) e numeri concreti.\n"
        "Basati solo sui dati qui sotto: se un dato manca, dillo invece di inventarlo. Collega sempre il consiglio "
        "allo stato di recupero (sonno, HRV, Body Battery, readiness) e alla scheda. Non sei un medico: per dolore, "
        "infortuni o sintomi strani suggerisci di sentire un medico o un fisioterapista.\n\n"
        f"Regole della scheda:\n{rules}\n\n"
        f"Dati aggiornati:\n{render_context(snapshot)}"
    )


def offline_reply(question: str, snapshot: dict[str, Any]) -> str:
    """Rule-based answers used when no language model is available."""
    q = question.lower()
    plan = snapshot["plan"]
    last_night = snapshot["wellness"][0] if snapshot["wellness"] else None
    sections = []

    def loads(which: str) -> str:
        workout = plan["workouts"][which]
        rows = [f"**{workout['title']}**"]
        for e in workout["exercises"]:
            rows.append(f"- {e['name']}: " + ", ".join(_set_text(s) for s in e["suggestion"]["sets"])
                        + f" ({e['suggestion']['message']})")
        warmup = workout["exercises"][0]["suggestion"]["warmup"]
        if warmup:
            rows.append("Riscaldamento: " + ", ".join(_set_text(s) for s in warmup) + ".")
        return "\n".join(rows)

    if last_night and any(k in q for k in ("stanc", "dormit", "sonno", "recuper", "hrv", "battery", "energia", "pezzi")):
        readiness = last_night["readiness_score"]
        if readiness is None:
            advice = "Non ho la readiness di oggi: regolati sul sonno e su come ti senti."
        elif readiness >= 60:
            advice = "Recupero buono: puoi allenarti come da scheda."
        else:
            advice = ("Recupero basso: allenati lo stesso ma accorcia i complementari, non i principali. "
                      "Se è giorno di corsa di qualità, falla più corta o trasformala in corsa facile.")
        sections.append(
            f"Stanotte hai dormito {_duration(last_night['sleep_seconds'])} (punteggio {_kg(last_night['sleep_score'])}), "
            f"HRV {_kg(last_night['hrv_last_night_ms'])} ms ({last_night['hrv_status'] or 'n.d.'}), "
            f"Body Battery al risveglio {_kg(last_night['body_battery_wake'])}, readiness {_kg(readiness)}. {advice}"
        )
    if any(k in q for k in ("settiman", "andata", "riepilog", "fatto")):
        week_ago = (snapshot["today"] - timedelta(days=6)).isoformat()
        km = sum((a["distance_m"] or 0) for a in snapshot["activities"] if a["sport"] == "run" and a["start_time_local"] >= week_ago) / 1000
        km_text = f"{km:.1f}".replace(".", ",")
        week = snapshot["week"]
        sections.append(
            f"Negli ultimi 7 giorni: {week['gym']} sessioni di palestra su {WEEKLY_TARGET['gym']} e {week['run']} corse "
            f"su {WEEKLY_TARGET['run']}, per {km_text} km di corsa."
        )
    if any(k in q for k in ("carich", "peso", "kg", "panca", "chin", "rematore", "curl", "oggi", "workout", "palestra")):
        intro = ""
        if plan["done_today"] and plan["last_workout"]:
            intro = f"Oggi hai già fatto il {plan['last_workout']['title']}. Ecco i carichi per il prossimo:\n"
        sections.append(intro + loads(plan["next_workout"]))
    if not sections:
        status = (f" Stanotte {_duration(last_night['sleep_seconds'])} di sonno, readiness {_kg(last_night['readiness_score'])}."
                  if last_night else "")
        sections.append(
            f"{_next_line(plan)}{status} Chiedimi i carichi, come stai recuperando o com'è andata la settimana."
        )
    return "\n\n".join([*sections, OFFLINE_NOTE])


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode())


def _get_json(url: str, timeout: float) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode())


def _llm_error(exc: Exception, service: str) -> CoachUnavailable:
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code in (401, 403):
            return CoachUnavailable(f"{service} rifiuta la chiave: è scaduta o non ha il permesso giusto.")
        if exc.code == 413:
            return CoachUnavailable("La conversazione è troppo lunga per il modello AI: tocca Nuova chat e riprova.")
        if exc.code == 429:
            return CoachUnavailable(
                "Hai fatto tante domande in poco tempo e il servizio AI chiede una pausa: riprova tra un po' "
                "(il piano gratuito ha un limite al minuto e uno al giorno)."
            )
        detail = exc.read().decode(errors="replace")[:300]
        return CoachUnavailable(f"{service} ha risposto con un errore ({exc.code}): {detail}")
    return CoachUnavailable(f"{service} non raggiungibile: {exc}")


class LLMClient:
    """OpenAI-compatible chat completions (OpenAI, Gemini, Anthropic, OpenRouter…), for paid API keys."""

    def __init__(self, settings: Settings, post: Callable[..., dict[str, Any]] = _post_json) -> None:
        self.settings = settings
        self._post = post

    @property
    def model(self) -> str | None:
        return self.settings.llm_model

    def complete(self, messages: list[dict[str, str]]) -> str:
        try:
            data = self._post(
                f"{self.settings.llm_base_url}/chat/completions",
                {"model": self.settings.llm_model, "messages": messages},
                {"Authorization": f"Bearer {self.settings.llm_api_key}"},
                self.settings.llm_timeout_s,
            )
        except (urllib.error.URLError, TimeoutError) as exc:
            raise _llm_error(exc, "Il modello AI") from exc
        try:
            return str(data["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise CoachUnavailable("Risposta del modello AI in un formato inatteso.") from exc


class OllamaClient:
    """A local Ollama server: free, no account, the data never leaves the computer."""

    _CACHE_S = 30.0

    def __init__(
        self,
        settings: Settings,
        get: Callable[..., dict[str, Any]] = _get_json,
        post: Callable[..., dict[str, Any]] = _post_json,
    ) -> None:
        self.settings = settings
        self._get = get
        self._post = post
        self._checked_at = float("-inf")
        self._model: str | None = None

    @property
    def model(self) -> str | None:
        """The model to chat with, or None when Ollama isn't running or has no chat model installed."""
        if time.monotonic() - self._checked_at > self._CACHE_S:
            self._model = self._find_model()
            self._checked_at = time.monotonic()
        return self._model

    def _find_model(self) -> str | None:
        try:
            tags = self._get(f"{self.settings.ollama_url}/api/tags", 2.0)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return None
        installed = [m.get("name", "") for m in tags.get("models") or [] if "embed" not in m.get("name", "")]
        wanted = self.settings.ollama_model
        if wanted:
            matches = [n for n in installed if n == wanted or n == f"{wanted}:latest"]
            return matches[0] if matches else None
        for family in PREFERRED_OLLAMA_MODELS:
            for name in installed:
                if name.startswith(family):
                    return name
        return installed[0] if installed else None

    def complete(self, messages: list[dict[str, str]]) -> str:
        model = self.model
        if model is None:
            raise CoachUnavailable("Ollama non è attivo o non ha modelli installati.")
        try:
            data = self._post(
                f"{self.settings.ollama_url}/api/chat",
                {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    # Thinking models (e.g. Qwen 3) would otherwise spend a long time reasoning before answering.
                    "think": False,
                    "options": {"num_ctx": self.settings.ollama_num_ctx},
                },
                {},
                self.settings.llm_timeout_s,
            )
        except (urllib.error.URLError, TimeoutError) as exc:
            self._checked_at = float("-inf")
            raise _llm_error(exc, "Ollama") from exc
        try:
            content = str(data["message"]["content"])
        except (KeyError, TypeError) as exc:
            raise CoachUnavailable("Risposta di Ollama in un formato inatteso.") from exc
        return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()


class Coach:
    """Picks who answers: a paid API if configured, else a local Ollama model, else offline rules."""

    def __init__(self, settings: Settings, api: LLMClient | None = None, ollama: OllamaClient | None = None) -> None:
        self.settings = settings
        self.api = api or LLMClient(settings)
        self.ollama = ollama or OllamaClient(settings)

    def status(self) -> dict[str, str | None]:
        if self.settings.llm_api_key and self.settings.llm_model:
            return {"mode": "api", "model": self.settings.llm_model}
        model = self.ollama.model
        return {"mode": "ollama", "model": model} if model else {"mode": "offline", "model": None}

    def reply(self, db: Database, text: str, *, today: date) -> list[dict[str, Any]]:
        """Store the user's message, answer it and store the answer. Returns both messages."""
        history = chat_history(db, limit=self.settings.chat_history_messages)
        user_message = _add_message(db, "user", text)
        snapshot = build_snapshot(db, self.settings, today)
        mode = self.status()["mode"]
        if mode == "offline":
            answer = offline_reply(text, snapshot)
        else:
            client = self.api if mode == "api" else self.ollama
            messages = [{"role": "system", "content": system_prompt(snapshot)}]
            messages += [{"role": m["role"], "content": m["content"]} for m in history]
            messages.append({"role": "user", "content": text})
            answer = client.complete(messages)
        return [user_message, _add_message(db, "assistant", answer)]


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def chat_history(db: Database, limit: int = 200) -> list[dict[str, Any]]:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT * FROM (SELECT id, role, content, created_at FROM chat_messages ORDER BY id DESC LIMIT ?) ORDER BY id",
            [limit],
        ).fetchall()
    return [dict(r) for r in rows]


def _add_message(db: Database, role: str, content: str) -> dict[str, Any]:
    created_at = _now_utc()
    with db.connect() as conn:
        cursor = conn.execute(
            "INSERT INTO chat_messages (role, content, created_at) VALUES (?, ?, ?)", [role, content, created_at]
        )
    return {"id": cursor.lastrowid, "role": role, "content": content, "created_at": created_at}


def clear_chat(db: Database) -> None:
    with db.connect() as conn:
        conn.execute("DELETE FROM chat_messages")
