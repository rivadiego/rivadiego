"""Where the plan meets the log: today's session, the week, next loads."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta
from typing import Any

from .config import Settings
from .db import Database
from .exercises import EXERCISES
from .plan import (
    ABS_CIRCUIT,
    GYM,
    NUTRITION,
    PHASES,
    RULES,
    SESSIONS,
    WEEKDAYS,
    WORKOUTS,
    is_ramp_up,
    monday_of,
    phase_for,
    rotation_session,
    scheme_label,
    week_number,
    workout_exercises,
)
from .progression import suggest, suggest_free, warmup_sets
from .wellness import latest_weight
from .workouts import done_by_day, first_workout_date, last_plan_workout, last_sets


def plan_start(db: Database, settings: Settings, today: date) -> date:
    """PLAN_START_DATE, else the week of the first logged workout (remembered), else this week."""
    if settings.plan_start_date:
        return settings.plan_start_date
    stored = db.get_meta("plan_start_date")
    if stored:
        return date.fromisoformat(stored)
    first = first_workout_date(db)
    if first is None:
        return monday_of(today)
    start = monday_of(first)
    db.set_meta("plan_start_date", start.isoformat())
    return start


def bodyweight(db: Database, settings: Settings) -> float | None:
    weight = latest_weight(db)
    return weight[1] if weight else settings.athlete_weight_kg


def next_gym_workout(db: Database, start: date, today: date) -> str:
    """The gym workout to do next. A and B alternate session after session, so a missed day
    doesn't break the sequence."""
    last = last_plan_workout(db)
    if last is not None:
        return _other(last[0])
    day = today
    while rotation_session(start, day) not in GYM:
        day += timedelta(days=1)
    return rotation_session(start, day)


def _session(key: str) -> dict[str, Any]:
    return {"key": key, **SESSIONS[key]}


def _other(which: str) -> str:
    return "B" if which == "A" else "A"


def week_overview(db: Database, start: date, today: date) -> list[dict[str, Any]]:
    monday = monday_of(today)
    done = done_by_day(db, monday, monday + timedelta(days=6))
    following = next_gym_workout(db, start, today)
    days = []
    for offset in range(7):
        day = monday + timedelta(days=offset)
        key = rotation_session(start, day)
        record = done.get(day.isoformat(), {})
        if record.get("plan_workout"):
            key = record["plan_workout"]
        elif key in GYM and day >= today:
            key = following
            following = _other(following)
        kind = SESSIONS[key]["kind"]
        days.append(
            {
                "date": day.isoformat(),
                "weekday": WEEKDAYS[day.weekday()],
                "is_today": day == today,
                "done": bool(record.get(kind)) if kind in {"gym", "run"} else False,
                **_session(key),
            }
        )
    return days


def _set_dicts(sets: list[Any]) -> list[dict[str, Any]]:
    return [asdict(s) for s in sets]


def workout_template(db: Database, settings: Settings, which: str, start: date, today: date) -> dict[str, Any]:
    week = week_number(start, today)
    ramp_up = is_ramp_up(week)
    weight = bodyweight(db, settings)
    exercises = []
    for index, item in enumerate(workout_exercises(which, week)):
        exercise = EXERCISES[item["exercise_id"]]
        previous = last_sets(db, exercise.id)
        last = previous[1] if previous else []
        suggestion = suggest(item, exercise, last, ramp_up=ramp_up, bodyweight=weight)
        warmup = warmup_sets(exercise, suggestion.sets[0].weight_kg) if index == 0 else []
        exercises.append(
            {
                "exercise_id": exercise.id,
                "name": exercise.name,
                "group": exercise.group,
                "equipment": exercise.equipment,
                "measure": exercise.measure,
                "scheme": item["scheme"],
                "scheme_label": scheme_label(item),
                "rep_range": item["rep_range"],
                "rest_s": item["rest_s"],
                "main": item["main"],
                "cue": item["cue"],
                "last": _set_dicts(last),
                "last_date": previous[0][:10] if previous else None,
                "suggestion": {
                    "message": suggestion.message,
                    "progressed": suggestion.progressed,
                    "sets": _set_dicts(suggestion.sets),
                    "warmup": _set_dicts(warmup),
                },
            }
        )
    abs_exercises = []
    for item in ABS_CIRCUIT["exercises"]:
        exercise = EXERCISES[item["exercise_id"]]
        previous = last_sets(db, exercise.id)
        last = previous[1] if previous else []
        suggestion = suggest_free(last)
        abs_exercises.append(
            {
                "exercise_id": exercise.id,
                "name": exercise.name,
                "group": exercise.group,
                "equipment": exercise.equipment,
                "measure": exercise.measure,
                "scheme": "circuit",
                "scheme_label": item["target"],
                "rep_range": None,
                "rest_s": 0,
                "main": False,
                "cue": item["cue"],
                "last": _set_dicts(last),
                "last_date": previous[0][:10] if previous else None,
                "suggestion": {
                    "message": suggestion.message,
                    "progressed": False,
                    "sets": _set_dicts(suggestion.sets if last else suggestion.sets * 2),
                    "warmup": [],
                },
            }
        )
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
    start = plan_start(db, settings, today)
    week = week_number(start, today)
    days = week_overview(db, start, today)
    today_entry = next(d for d in days if d["is_today"])
    return {
        "name": "Scheda Hybrid Athlete",
        "subtitle": "Upper body · 3 palestra + 2 corse",
        "start_date": start.isoformat(),
        "week": week,
        "phase": phase_for(week),
        "phases": PHASES,
        "today": today_entry,
        "next_gym_workout": next_gym_workout(db, start, today),
        "days": days,
        "workouts": {key: workout_template(db, settings, key, start, today) for key in GYM},
        "rules": RULES,
        "nutrition": NUTRITION,
        "bodyweight_kg": bodyweight(db, settings),
    }
