"""The personal trainer chat: context built from the plan, the log and the vital signs."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from typing import Any

from .config import Settings
from .db import Database
from .planner import plan_payload
from .plan import RULES, WEEKDAYS
from .sources import SourceError
from .wellness import wellness_rows
from .workouts import feed, workouts_since

MONTHS = ("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre",
          "novembre", "dicembre")
OFFLINE_NOTE = (
    "*Coach offline: rispondo con regole automatiche sui tuoi dati. Collega un modello AI nel backend "
    "per parlare liberamente (vedi README).*"
)


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


def build_snapshot(db: Database, settings: Settings, today: date) -> dict[str, Any]:
    since = (today - timedelta(days=13)).isoformat()
    return {
        "today": today,
        "athlete": {
            "name": settings.athlete_name,
            "height_cm": settings.athlete_height_cm,
        },
        "plan": plan_payload(db, settings, today),
        "wellness": wellness_rows(db, today=today, days=settings.wellness_days),
        "activities": [a for a in feed(db, limit=60, since_local=since) if a["source"] == "garmin"],
        "workouts": workouts_since(db, since),
    }


def render_context(snapshot: dict[str, Any]) -> str:
    today: date = snapshot["today"]
    plan = snapshot["plan"]
    athlete = snapshot["athlete"]
    lines = [
        f"Oggi è {WEEKDAYS[today.weekday()].lower()} {today.day} {MONTHS[today.month - 1]} {today.year}.",
        f"Programma: {plan['name']} ({plan['subtitle']}), settimana {plan['week']}, fase \"{plan['phase']['name']}\": "
        f"{plan['phase']['text']}",
        f"Sessione prevista oggi: {plan['today']['title']}"
        + (" (già fatta)." if plan["today"]["done"] else ".")
        + f" Prossimo workout in palestra: {plan['next_gym_workout']}.",
    ]
    profile = [part for part in (
        athlete.get("name"),
        f"{athlete['height_cm']:g} cm" if athlete.get("height_cm") else None,
        f"{_kg(plan['bodyweight_kg'])} kg" if plan.get("bodyweight_kg") else None,
    ) if part]
    if profile:
        lines.append("Atleta: " + ", ".join(profile) + ".")
    lines.append("Settimana: " + "; ".join(
        f"{d['weekday'][:3]} {d['title']}{' ✓' if d['done'] else ''}" for d in plan["days"]
    ))

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
    for key, workout in plan["workouts"].items():
        parts = []
        for e in workout["exercises"]:
            sets = ", ".join(_set_text(s) for s in e["suggestion"]["sets"])
            parts.append(f"{e['name']} {sets} — {e['suggestion']['message']}")
        lines.append(f"{workout['title']}: " + " | ".join(parts))
    return "\n".join(lines)


def system_prompt(snapshot: dict[str, Any]) -> str:
    rules = "\n".join(f"- {r['title']}: {r['text']}" for r in RULES)
    name = snapshot["athlete"].get("name") or "l'atleta"
    return (
        f"Sei il personal trainer di {name}, un atleta ibrido (palestra upper body + corsa). Parli in italiano, "
        "in modo diretto, pratico e motivante, con risposte brevi (massimo 8-10 righe) e numeri concreti.\n"
        "Basati solo sui dati qui sotto: se un dato manca, dillo invece di inventarlo. Collega sempre il consiglio "
        "allo stato di recupero (sonno, HRV, Body Battery, readiness) e alla scheda. Non sei un medico: per dolore, "
        "infortuni o sintomi strani suggerisci di sentire un medico o un fisioterapista.\n\n"
        f"Regole della scheda:\n{rules}\n\n"
        f"Dati aggiornati:\n{render_context(snapshot)}"
    )


def offline_reply(question: str, snapshot: dict[str, Any]) -> str:
    """Rule-based answers used when no language model is configured."""
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
        done = [d for d in plan["days"] if d["done"]]
        planned = [d for d in plan["days"] if d["kind"] != "rest"]
        week_ago = (snapshot["today"] - timedelta(days=6)).isoformat()
        km = sum((a["distance_m"] or 0) for a in snapshot["activities"] if a["sport"] == "run" and a["start_time_local"] >= week_ago) / 1000
        km_text = f"{km:.1f}".replace(".", ",")
        sections.append(
            f"Questa settimana hai completato {len(done)} sessioni su {len(planned)} previste "
            f"({', '.join(d['title'] for d in done) or 'nessuna ancora'}). Negli ultimi 7 giorni hai corso {km_text} km."
        )
    if any(k in q for k in ("carich", "peso", "kg", "panca", "chin", "rematore", "curl", "oggi", "workout", "palestra")):
        today = plan["today"]
        gym_today = today["kind"] == "gym" and not today["done"]
        which = today["key"] if gym_today else plan["next_gym_workout"]
        if gym_today:
            intro = ""
        elif today["kind"] == "gym":
            intro = f"Oggi hai già fatto il {today['title']}. Ecco i carichi per il prossimo:"
        else:
            intro = f"Oggi: {today['title']}. Per la prossima palestra:"
        sections.append((intro + "\n" if intro else "") + loads(which))
    if not sections:
        today = plan["today"]
        status = (f" Stanotte {_duration(last_night['sleep_seconds'])} di sonno, readiness {_kg(last_night['readiness_score'])}."
                  if last_night else "")
        sections.append(
            f"Oggi è in programma {today['title']}.{status} Chiedimi i carichi di oggi, come stai recuperando "
            "o com'è andata la settimana."
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


class LLMClient:
    """OpenAI-compatible chat completions (OpenAI, Gemini, Anthropic, OpenRouter, Ollama…)."""

    def __init__(self, settings: Settings, post: Callable[..., dict[str, Any]] = _post_json) -> None:
        self.settings = settings
        self._post = post

    def complete(self, messages: list[dict[str, str]]) -> str:
        try:
            data = self._post(
                f"{self.settings.llm_base_url}/chat/completions",
                {"model": self.settings.llm_model, "messages": messages},
                {"Authorization": f"Bearer {self.settings.llm_api_key}"},
                self.settings.llm_timeout_s,
            )
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300]
            raise CoachUnavailable(f"Il modello AI ha risposto con un errore ({exc.code}): {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise CoachUnavailable(f"Modello AI non raggiungibile: {exc}") from exc
        try:
            return str(data["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise CoachUnavailable("Risposta del modello AI in un formato inatteso.") from exc


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


def reply(
    db: Database, settings: Settings, text: str, *, today: date, llm: LLMClient | None = None
) -> list[dict[str, Any]]:
    """Store the user's message, answer it and store the answer. Returns both messages."""
    history = chat_history(db, limit=settings.chat_history_messages)
    user_message = _add_message(db, "user", text)
    snapshot = build_snapshot(db, settings, today)
    if settings.llm_configured:
        client = llm or LLMClient(settings)
        messages = [{"role": "system", "content": system_prompt(snapshot)}]
        messages += [{"role": m["role"], "content": m["content"]} for m in history]
        messages.append({"role": "user", "content": text})
        answer = client.complete(messages)
    else:
        answer = offline_reply(text, snapshot)
    return [user_message, _add_message(db, "assistant", answer)]
