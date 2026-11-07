from datetime import datetime

import pytest
from helpers import make_raw

from coach_connect.db import Database
from coach_connect.normalize import normalize_activity
from coach_connect.progression import LoggedSet
from coach_connect.workouts import create_workout, delete_workout, feed, feed_count, get_workout, last_sets


@pytest.fixture
def db(tmp_path):
    return Database(tmp_path / "workouts.db")


def store_garmin(db, raw):
    db.upsert_activities([{**normalize_activity(raw), "synced_at": "2026-10-20T08:00:00Z"}])


def push_workout(db, local="2026-10-19 07:10:00", utc="2026-10-19 05:10:00"):
    return create_workout(
        db,
        name="Workout A · Push",
        plan_workout="A",
        start_local=datetime.fromisoformat(local),
        start_utc=datetime.fromisoformat(utc),
        duration_s=3300,
        notes="Spalla ok",
        exercises=[
            ("incline_barbell_bench", [LoggedSet(60, 5), LoggedSet(54, 6), LoggedSet(48, 8)]),
            ("plank", [LoggedSet(None, None, 50), LoggedSet(None, None, 45)]),
        ],
    )


def test_logged_workout_round_trip(db):
    workout = get_workout(db, push_workout(db))

    assert workout["name"] == "Workout A · Push"
    assert [e["name"] for e in workout["exercises"]] == ["Panca inclinata bilanciere", "Plank"]
    assert workout["exercises"][1]["sets"][0]["seconds"] == 50
    assert workout["set_count"] == 5
    assert workout["volume_kg"] == 60 * 5 + 54 * 6 + 48 * 8
    assert last_sets(db, "incline_barbell_bench") == ("2026-10-19 07:10:00", [LoggedSet(60, 5), LoggedSet(54, 6), LoggedSet(48, 8)])


def test_feed_mixes_garmin_runs_and_logged_workouts_newest_first(db):
    run = make_raw(0)  # 2026-10-20 07:00 local
    store_garmin(db, run)
    push_workout(db)

    items = feed(db, limit=10)

    assert [(i["source"], i["name"]) for i in items] == [("garmin", "Attività 0"), ("manual", "Workout A · Push")]
    assert items[1]["exercise_count"] == 2 and items[1]["set_count"] == 5
    assert feed_count(db) == 2


def test_watch_strength_session_is_merged_into_the_logged_workout(db):
    strength = make_raw(3, activity_id=555, type_key="strength_training", name="Allenamento di forza")
    strength["startTimeGMT"] = "2026-10-19 05:02:00"
    strength["averageHR"] = 118.0
    store_garmin(db, strength)

    workout_id = push_workout(db)
    items = feed(db, limit=10)

    assert [(i["source"], i["id"]) for i in items] == [("manual", workout_id)]
    assert items[0]["garmin_linked"] and items[0]["avg_hr"] == 118.0
    assert get_workout(db, workout_id)["garmin_activity_id"] == 555


def test_delete_workout_removes_its_sets(db):
    workout_id = push_workout(db)

    assert delete_workout(db, workout_id)
    assert get_workout(db, workout_id) is None
    assert last_sets(db, "incline_barbell_bench") is None
    assert not delete_workout(db, workout_id)
