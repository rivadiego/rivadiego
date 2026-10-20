"""Where the plan meets the log: which workout is next and with which loads."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Any

from .config import Settings
from .db import Database
from .exercises import EXERCISES
from .plan import ABS_CIRCUIT, GYM, NUTRITION, RULES, WORKOUTS, other_workout, scheme_label, workout_exercises
from .progression import suggest, suggest_free, warmup_sets
from .wellness import latest_weight
from .workouts import last_plan_workout, last_sets


def bodyweight(db: Database, settings: Settings) -> float | None:
    weight = latest_weight(db)
    return weight[1] if weight else settings.athlete_weight_kg


def next_gym_workout(db: Database) -> str:
    """A and B alternate session after session, so a missed day doesn't break the sequence."""
    last = last_plan_workout(db)
    return other_workout(last[0]) if last else "A"


def _set_dicts(sets: list[Any]) -> list[dict[str, Any]]:
    return [asdict(s) for s in sets]


def _template_exercise(db: Database, item: dict[str, Any], suggestion_for: Any, *, first: bool) -> dict[str, Any]:
    exercise = EXERCISES[item["exercise_id"]]
    previous = last_sets(db, exercise.id)
    last = previous[1] if previous else []
    suggestion = suggestion_for(exercise, last)
    warmup = warmup_sets(exercise, suggestion.sets[0].weight_kg) if first else []
    return {
        "exercise_id": exercise.id,
        "name": exercise.name,
        "group": exercise.group,
        "equipment": exercise.equipment,
        "measure": exercise.measure,
        "scheme": item.get("scheme", "circuit"),
        "scheme_label": scheme_label(item) if "scheme" in item else item["target"],
        "rep_range": item.get("rep_range"),
        "rest_s": item.get("rest_s", 0),
        "main": item.get("main", False),
        "cue": item["cue"],
        "last": _set_dicts(last),
        "last_date": previous[0][:10] if previous else None,
        "suggestion": {
            "message": suggestion.message,
            "progressed": suggestion.progressed,
            "sets": _set_dicts(suggestion.sets if last or "scheme" in item else suggestion.sets * 2),
            "warmup": _set_dicts(warmup),
        },
    }


def workout_template(db: Database, settings: Settings, which: str) -> dict[str, Any]:
    weight = bodyweight(db, settings)
    exercises = [
        _template_exercise(
            db,
            item,
            lambda exercise, last, item=item: suggest(item, exercise, last, bodyweight=weight),
            first=index == 0,
        )
        for index, item in enumerate(workout_exercises(which))
    ]
    abs_exercises = [
        _template_exercise(db, item, lambda _exercise, last: suggest_free(last), first=False)
        for item in ABS_CIRCUIT["exercises"]
    ]
    return {
        "key": which,
        "title": WORKOUTS[which]["title"],
        "focus": WORKOUTS[which]["focus"],
        "exercises": exercises,
        "abs": abs_exercises,
        "abs_rounds": ABS_CIRCUIT["rounds"],
        "abs_rest": ABS_CIRCUIT["rest"],
    }


def plan_payload(db: Database, settings: Settings, today: date) -> dict[str, Any]:
    last = last_plan_workout(db)
    return {
        "name": "Scheda Hybrid Athlete",
        "subtitle": "Upper body · A e B a giorni alterni",
        "next_workout": next_gym_workout(db),
        "last_workout": (
            {"key": last[0], "title": WORKOUTS[last[0]]["title"], "date": last[1][:10]} if last else None
        ),
        "done_today": bool(last and last[1][:10] == today.isoformat()),
        "workouts": {key: workout_template(db, settings, key) for key in GYM},
        "rules": RULES,
        "nutrition": NUTRITION,
        "bodyweight_kg": bodyweight(db, settings),
    }
