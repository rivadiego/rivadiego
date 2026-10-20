"""Gym sessions logged in the app, and the activity feed that mixes them with Garmin activities."""

from __future__ import annotations

import random
from collections.abc import Sequence
from datetime import date, datetime, timedelta, timezone
from typing import Any

from .db import Database
from .exercises import EXERCISES
from .plan import ABS_CIRCUIT, WORKOUTS, is_ramp_up, monday_of, week_number, workout_exercises
from .progression import LoggedSet, SetTarget, suggest

# A logged gym session and a Garmin strength activity this close in time are the same workout.
LINK_WINDOW = timedelta(hours=4)
_TS = "%Y-%m-%d %H:%M:%S"


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def create_workout(
    db: Database,
    *,
    name: str,
    plan_workout: str | None,
    start_local: datetime,
    start_utc: datetime,
    duration_s: float | None,
    notes: str | None,
    exercises: Sequence[tuple[str, Sequence[LoggedSet]]],
) -> int:
    with db.connect() as conn:
        cursor = conn.execute(
            "INSERT INTO workouts (name, plan_workout, start_time_local, start_time_gmt, duration_s, notes, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [name, plan_workout, start_local.strftime(_TS), start_utc.strftime(_TS), duration_s, notes, _now_utc()],
        )
        workout_id = int(cursor.lastrowid)
        conn.executemany(
            "INSERT INTO workout_sets (workout_id, position, exercise_id, set_index, weight_kg, reps, seconds) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (workout_id, position, exercise_id, index, s.weight_kg, s.reps, s.seconds)
                for position, (exercise_id, sets) in enumerate(exercises)
                for index, s in enumerate(sets)
            ],
        )
    link_garmin_activities(db)
    return workout_id


def delete_workout(db: Database, workout_id: int) -> bool:
    with db.connect() as conn:
        return conn.execute("DELETE FROM workouts WHERE id = ?", [workout_id]).rowcount > 0


def _exercise_blocks(rows: Sequence[Any]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for row in rows:
        if not blocks or blocks[-1]["position"] != row["position"]:
            exercise = EXERCISES.get(row["exercise_id"])
            blocks.append(
                {
                    "position": row["position"],
                    "exercise_id": row["exercise_id"],
                    "name": exercise.name if exercise else row["exercise_id"],
                    "measure": exercise.measure if exercise else "reps",
                    "sets": [],
                }
            )
        blocks[-1]["sets"].append({"weight_kg": row["weight_kg"], "reps": row["reps"], "seconds": row["seconds"]})
    return blocks


def get_workout(db: Database, workout_id: int) -> dict[str, Any] | None:
    with db.connect() as conn:
        workout = conn.execute(
            "SELECT w.*, a.duration_s AS garmin_duration_s, a.avg_hr, a.max_hr, a.calories "
            "FROM workouts w LEFT JOIN activities a ON a.id = w.garmin_activity_id WHERE w.id = ?",
            [workout_id],
        ).fetchone()
        if workout is None:
            return None
        sets = conn.execute(
            "SELECT * FROM workout_sets WHERE workout_id = ? ORDER BY position, set_index", [workout_id]
        ).fetchall()
    exercises = _exercise_blocks(sets)
    return {
        "id": workout["id"],
        "name": workout["name"],
        "plan_workout": workout["plan_workout"],
        "start_time_local": workout["start_time_local"],
        "start_time_gmt": workout["start_time_gmt"],
        "duration_s": workout["garmin_duration_s"] or workout["duration_s"],
        "notes": workout["notes"],
        "garmin_activity_id": workout["garmin_activity_id"],
        "avg_hr": workout["avg_hr"],
        "max_hr": workout["max_hr"],
        "calories": workout["calories"],
        "exercises": exercises,
        "set_count": sum(len(e["sets"]) for e in exercises),
        "volume_kg": round(sum((s["weight_kg"] or 0) * (s["reps"] or 0) for e in exercises for s in e["sets"]), 1),
    }


def last_sets(db: Database, exercise_id: str) -> tuple[str, list[LoggedSet]] | None:
    """Sets of the most recent workout containing the exercise, with that workout's local start time."""
    with db.connect() as conn:
        workout = conn.execute(
            "SELECT w.id, w.start_time_local FROM workouts w JOIN workout_sets s ON s.workout_id = w.id "
            "WHERE s.exercise_id = ? ORDER BY w.start_time_gmt DESC, w.id DESC LIMIT 1",
            [exercise_id],
        ).fetchone()
        if workout is None:
            return None
        rows = conn.execute(
            "SELECT weight_kg, reps, seconds FROM workout_sets WHERE workout_id = ? AND exercise_id = ? ORDER BY set_index",
            [workout["id"], exercise_id],
        ).fetchall()
    return workout["start_time_local"], [LoggedSet(r["weight_kg"], r["reps"], r["seconds"]) for r in rows]


def last_plan_workout(db: Database) -> tuple[str, str] | None:
    """(A or B, local start time) of the most recent logged plan workout."""
    with db.connect() as conn:
        row = conn.execute(
            "SELECT plan_workout, start_time_local FROM workouts WHERE plan_workout IN ('A', 'B') "
            "ORDER BY start_time_gmt DESC, id DESC LIMIT 1"
        ).fetchone()
    return (row["plan_workout"], row["start_time_local"]) if row else None


def first_workout_date(db: Database) -> date | None:
    with db.connect() as conn:
        row = conn.execute("SELECT MIN(start_time_local) AS first FROM workouts").fetchone()
    return date.fromisoformat(row["first"][:10]) if row and row["first"] else None


def done_by_day(db: Database, start: date, end: date) -> dict[str, dict[str, Any]]:
    """What was trained each day between two dates: logged plan workouts, gym sessions and runs."""
    days: dict[str, dict[str, Any]] = {}
    with db.connect() as conn:
        for row in conn.execute(
            "SELECT substr(start_time_local, 1, 10) AS day, plan_workout FROM workouts "
            "WHERE substr(start_time_local, 1, 10) BETWEEN ? AND ?",
            [start.isoformat(), end.isoformat()],
        ):
            entry = days.setdefault(row["day"], {"gym": False, "run": False, "plan_workout": None})
            entry["gym"] = True
            entry["plan_workout"] = entry["plan_workout"] or row["plan_workout"]
        for row in conn.execute(
            "SELECT substr(start_time_local, 1, 10) AS day, sport FROM activities "
            "WHERE substr(start_time_local, 1, 10) BETWEEN ? AND ? AND sport IN ('run', 'strength')",
            [start.isoformat(), end.isoformat()],
        ):
            entry = days.setdefault(row["day"], {"gym": False, "run": False, "plan_workout": None})
            entry["run" if row["sport"] == "run" else "gym"] = True
    return days


def link_garmin_activities(db: Database) -> int:
    """Attach each logged workout to the Garmin strength activity recorded at the same time."""
    linked = 0
    with db.connect() as conn:
        taken = {r[0] for r in conn.execute("SELECT garmin_activity_id FROM workouts WHERE garmin_activity_id IS NOT NULL")}
        pending = conn.execute("SELECT id, start_time_gmt FROM workouts WHERE garmin_activity_id IS NULL").fetchall()
        for workout in pending:
            start = datetime.strptime(workout["start_time_gmt"], _TS)
            candidates = conn.execute(
                "SELECT id, start_time_gmt FROM activities WHERE sport = 'strength' AND start_time_gmt BETWEEN ? AND ?",
                [(start - LINK_WINDOW).strftime(_TS), (start + LINK_WINDOW).strftime(_TS)],
            ).fetchall()
            best = min(
                (c for c in candidates if c["id"] not in taken),
                key=lambda c: abs(datetime.strptime(c["start_time_gmt"], _TS) - start),
                default=None,
            )
            if best is not None:
                conn.execute("UPDATE workouts SET garmin_activity_id = ? WHERE id = ?", [best["id"], workout["id"]])
                taken.add(best["id"])
                linked += 1
    return linked


_FEED_SQL = """
SELECT 'garmin' AS source, a.id, a.name, a.sport, a.type_key, a.start_time_local, a.start_time_gmt,
       a.duration_s, a.distance_m, a.elevation_gain_m, a.avg_speed_mps, a.avg_hr, a.max_hr, a.calories, a.location,
       NULL AS plan_workout, NULL AS exercise_count, NULL AS set_count, NULL AS volume_kg, 0 AS garmin_linked
FROM activities a
WHERE NOT EXISTS (SELECT 1 FROM workouts w WHERE w.garmin_activity_id = a.id)
UNION ALL
SELECT 'manual', w.id, w.name, 'strength', 'strength_training', w.start_time_local, w.start_time_gmt,
       COALESCE(a.duration_s, w.duration_s), NULL, NULL, NULL, a.avg_hr, a.max_hr, a.calories, NULL,
       w.plan_workout,
       (SELECT COUNT(DISTINCT position) FROM workout_sets s WHERE s.workout_id = w.id),
       (SELECT COUNT(*) FROM workout_sets s WHERE s.workout_id = w.id),
       (SELECT ROUND(SUM(COALESCE(s.weight_kg, 0) * COALESCE(s.reps, 0)), 1) FROM workout_sets s WHERE s.workout_id = w.id),
       w.garmin_activity_id IS NOT NULL
FROM workouts w LEFT JOIN activities a ON a.id = w.garmin_activity_id
"""


def feed(db: Database, *, limit: int, offset: int = 0, since_local: str | None = None) -> list[dict[str, Any]]:
    where = "WHERE start_time_local >= ?" if since_local else ""
    params: list[Any] = [since_local] if since_local else []
    with db.connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM ({_FEED_SQL}) {where} ORDER BY start_time_gmt DESC, source, id DESC LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()
    return [dict(r) for r in rows]


def feed_count(db: Database) -> int:
    with db.connect() as conn:
        return conn.execute(f"SELECT COUNT(*) FROM ({_FEED_SQL})").fetchone()[0]


def workouts_since(db: Database, since_local: str) -> list[dict[str, Any]]:
    """Logged workouts with their sets, oldest first, for the coach."""
    with db.connect() as conn:
        ids = [r["id"] for r in conn.execute(
            "SELECT id FROM workouts WHERE start_time_local >= ? ORDER BY start_time_gmt", [since_local]
        )]
    return [w for w in (get_workout(db, workout_id) for workout_id in ids) if w]


_DEMO_START_LOADS = {
    "incline_barbell_bench": 55.0,
    "lateral_raise": 8.0,
    "dumbbell_bench_press": 22.0,
    "cable_pushdown": 20.0,
    "weighted_chin_up": 5.0,
    "dumbbell_row": 24.0,
    "seated_rear_delt_raise": 6.0,
    "barbell_curl": 25.0,
}
_DEMO_ABS = {"jackknife_crunch": (14, 20), "lying_leg_raise": (12, 15), "russian_twist": (12, 16), "plank": (45, 60)}


def seed_demo_workouts(db: Database, *, bodyweight: float, weeks: int = 5) -> int:
    """Log plan workouts for the demo's Garmin gym sessions, progressing with the real plan rules."""
    if first_workout_date(db) is not None:
        return 0
    rng = random.Random(42)
    start = monday_of(date.today()) - timedelta(weeks=weeks)
    if db.get_meta("plan_start_date") is None:
        db.set_meta("plan_start_date", start.isoformat())
    plan_start = date.fromisoformat(db.get_meta("plan_start_date") or start.isoformat())
    with db.connect() as conn:
        sessions = conn.execute(
            "SELECT name, start_time_local, start_time_gmt, duration_s FROM activities "
            "WHERE sport = 'strength' AND start_time_local >= ? ORDER BY start_time_gmt",
            [start.isoformat()],
        ).fetchall()
    history: dict[str, list[LoggedSet]] = {}
    created = 0
    for session in sessions:
        which = "A" if "Push" in session["name"] else "B" if "Pull" in session["name"] else None
        if which is None:
            continue
        week = week_number(plan_start, date.fromisoformat(session["start_time_local"][:10]))
        logged: list[tuple[str, list[LoggedSet]]] = []
        for item in workout_exercises(which, week):
            exercise = EXERCISES[item["exercise_id"]]
            last = history.get(exercise.id)
            if last:
                targets = suggest(item, exercise, last, ramp_up=is_ramp_up(week), bodyweight=bodyweight).sets
            else:
                load = _DEMO_START_LOADS.get(exercise.id, 10.0)
                reps = item["reps"] or [item["rep_range"][0]] * item["sets"]
                targets = [SetTarget(load, r) for r in reps]
            performed = []
            for target in targets:
                goal = target.reps or (item["rep_range"] or [8, 12])[0]
                top = item["rep_range"][1] if item["rep_range"] else goal
                if item["scheme"] == "rpt":
                    reps_done = goal - 1 if rng.random() < 0.2 else goal
                else:
                    reps_done = min(top, goal + rng.choice((0, 1, 1, 2)))
                performed.append(LoggedSet(target.weight_kg, reps_done))
            history[exercise.id] = performed
            logged.append((exercise.id, performed))
        for abs_item in ABS_CIRCUIT["exercises"]:
            low, high = _DEMO_ABS[abs_item["exercise_id"]]
            if abs_item["exercise_id"] == "plank":
                logged.append(("plank", [LoggedSet(None, None, rng.randint(low, high)) for _ in range(2)]))
            else:
                logged.append((abs_item["exercise_id"], [LoggedSet(None, rng.randint(low, high)) for _ in range(2)]))
        local = datetime.strptime(session["start_time_local"], _TS)
        utc = datetime.strptime(session["start_time_gmt"], _TS)
        create_workout(
            db,
            name=WORKOUTS[which]["title"],
            plan_workout=which,
            start_local=local,
            start_utc=utc,
            duration_s=session["duration_s"],
            notes=None,
            exercises=logged,
        )
        created += 1
    return created
