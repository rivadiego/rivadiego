from datetime import date, datetime

import pytest

from coach_connect.config import Settings
from coach_connect.db import Database
from coach_connect.plan import phase_for, rotation_session, week_number, workout_exercises
from coach_connect.planner import next_gym_workout, plan_payload, plan_start, week_overview
from coach_connect.progression import LoggedSet
from coach_connect.workouts import create_workout

START = date(2026, 10, 5)  # a Monday


@pytest.fixture
def db(tmp_path):
    return Database(tmp_path / "plan.db")


def log(db, which, day, hour=7):
    when = datetime.fromisoformat(f"{day}T{hour:02d}:00:00")
    return create_workout(
        db,
        name=f"Workout {which}",
        plan_workout=which,
        start_local=when,
        start_utc=when,
        duration_s=None,
        notes=None,
        exercises=[("incline_barbell_bench" if which == "A" else "weighted_chin_up", [LoggedSet(50, 5)])],
    )


def test_two_week_rotation_alternates_a_and_b():
    week1 = [rotation_session(START, date(2026, 10, d)) for d in range(5, 12)]
    week2 = [rotation_session(START, date(2026, 10, d)) for d in range(12, 19)]

    assert week1 == ["A", "run_quality", "B", "rest", "A", "rest", "run_long"]
    assert week2 == ["B", "run_quality", "A", "rest", "B", "rest", "run_long"]


def test_weeks_and_phases():
    assert week_number(START, date(2026, 10, 11)) == 1
    assert week_number(START, date(2026, 10, 26)) == 4
    assert phase_for(3)["name"] == "Ripresa"
    assert phase_for(4)["name"] == "RPT pieno"
    assert phase_for(13)["name"] == "Variante"


def test_week_thirteen_swaps_in_the_variants():
    names = [e["exercise_id"] for e in workout_exercises("A", 13)]
    assert names == ["incline_barbell_bench", "lateral_raise", "military_press", "cable_french_press"]
    assert workout_exercises("B", 13)[0]["exercise_id"] == "weighted_pull_up"


def test_next_gym_workout_follows_the_log_not_the_calendar(db):
    assert next_gym_workout(db, START, date(2026, 10, 6)) == "B"  # nothing logged: Wednesday's rotation
    # Rotation says Friday 9 is A, but after A on Monday and a skipped Wednesday, B comes next.
    log(db, "A", "2026-10-05")
    assert next_gym_workout(db, START, date(2026, 10, 9)) == "B"
    log(db, "B", "2026-10-09")
    assert next_gym_workout(db, START, date(2026, 10, 9)) == "A"


def test_week_overview_marks_done_and_alternates_upcoming(db):
    log(db, "A", "2026-10-12")
    days = week_overview(db, START, date(2026, 10, 13))

    assert [(d["key"], d["done"]) for d in days] == [
        ("A", True),
        ("run_quality", False),
        ("B", False),
        ("rest", False),
        ("A", False),
        ("rest", False),
        ("run_long", False),
    ]
    assert days[1]["is_today"]


def test_plan_start_comes_from_settings_or_first_workout(db):
    assert plan_start(db, Settings(plan_start_date=START), date(2026, 10, 20)) == START
    log(db, "A", "2026-10-14")
    assert plan_start(db, Settings(), date(2026, 10, 20)) == date(2026, 10, 12)


def test_plan_payload_includes_templates_with_suggestions(db):
    log(db, "A", "2026-10-12")
    payload = plan_payload(db, Settings(plan_start_date=START), date(2026, 10, 13))

    assert payload["week"] == 2 and payload["phase"]["name"] == "Ripresa"
    incline = payload["workouts"]["A"]["exercises"][0]
    assert incline["scheme_label"] == "RPT 5/6/8"
    assert incline["last"] == [{"weight_kg": 50, "reps": 5, "seconds": None}]
    assert incline["suggestion"]["sets"][0]["weight_kg"] == 50
    assert payload["workouts"]["A"]["abs"][3]["measure"] == "seconds"


def test_timed_exercises_keep_their_seconds_in_the_suggestion(db):
    when = datetime.fromisoformat("2026-10-12T07:00:00")
    create_workout(db, name="A", plan_workout="A", start_local=when, start_utc=when, duration_s=None, notes=None,
                   exercises=[("plank", [LoggedSet(None, None, 55), LoggedSet(None, None, 50)])])

    plank = plan_payload(db, Settings(plan_start_date=START), date(2026, 10, 13))["workouts"]["A"]["abs"][3]

    assert [s["seconds"] for s in plank["suggestion"]["sets"]] == [55, 50]
