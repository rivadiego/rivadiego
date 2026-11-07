from datetime import date, datetime

import pytest

from coach_connect.config import Settings
from coach_connect.db import Database
from coach_connect.plan import workout_exercises
from coach_connect.planner import next_gym_workout, plan_payload
from coach_connect.progression import LoggedSet
from coach_connect.workouts import create_workout


@pytest.fixture
def db(tmp_path):
    return Database(tmp_path / "plan.db")


def log(db, which, day, exercises=None):
    when = datetime.fromisoformat(f"{day}T07:00:00")
    return create_workout(
        db,
        name=f"Workout {which}",
        plan_workout=which,
        start_local=when,
        start_utc=when,
        duration_s=None,
        notes=None,
        exercises=exercises or [("incline_barbell_bench" if which == "A" else "weighted_chin_up", [LoggedSet(50, 5)])],
    )


def test_workouts_a_and_b():
    assert [e["exercise_id"] for e in workout_exercises("A")] == [
        "incline_barbell_bench",
        "lateral_raise",
        "dumbbell_bench_press",
        "cable_pushdown",
    ]
    assert workout_exercises("B")[0]["name"] == "Chin-up zavorrate (presa supina)"


def test_a_and_b_alternate_following_the_log(db):
    assert next_gym_workout(db) == "A"
    log(db, "A", "2026-10-05")
    assert next_gym_workout(db) == "B"
    log(db, "B", "2026-10-09")
    assert next_gym_workout(db) == "A"


def test_plan_payload_has_next_and_last_workout_without_weeks(db):
    log(db, "A", "2026-10-12")

    payload = plan_payload(db, Settings(), date(2026, 10, 13))

    assert payload["next_workout"] == "B"
    assert payload["last_workout"] == {"key": "A", "title": "Workout A · Push", "date": "2026-10-12"}
    assert payload["done_today"] is False
    assert plan_payload(db, Settings(), date(2026, 10, 12))["done_today"] is True
    assert not {"week", "phase", "days", "today"} & set(payload)


def test_plan_payload_includes_templates_with_suggestions(db):
    log(db, "A", "2026-10-12")

    payload = plan_payload(db, Settings(), date(2026, 10, 13))

    incline = payload["workouts"]["A"]["exercises"][0]
    assert incline["scheme_label"] == "RPT 5/6/8"
    assert incline["last"] == [{"weight_kg": 50, "reps": 5, "seconds": None}]
    assert incline["suggestion"]["sets"][0]["weight_kg"] == 50
    assert incline["suggestion"]["warmup"]
    assert payload["workouts"]["A"]["abs"][3]["measure"] == "seconds"


def test_timed_exercises_keep_their_seconds_in_the_suggestion(db):
    log(db, "A", "2026-10-12", exercises=[("plank", [LoggedSet(None, None, 55), LoggedSet(None, None, 50)])])

    plank = plan_payload(db, Settings(), date(2026, 10, 13))["workouts"]["A"]["abs"][3]

    assert [s["seconds"] for s in plank["suggestion"]["sets"]] == [55, 50]
