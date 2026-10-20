"""Daily vital signs (sleep, HRV, Body Battery, resting HR, stress, readiness) for the coach."""

from __future__ import annotations

import json
import time
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from .db import Database

if TYPE_CHECKING:
    from .sources import ActivitySource

WELLNESS_FIELDS = (
    "date",
    "sleep_seconds",
    "deep_sleep_seconds",
    "rem_sleep_seconds",
    "light_sleep_seconds",
    "awake_seconds",
    "sleep_score",
    "hrv_last_night_ms",
    "hrv_weekly_avg_ms",
    "hrv_status",
    "resting_hr",
    "min_hr",
    "max_hr",
    "body_battery_high",
    "body_battery_low",
    "body_battery_wake",
    "stress_avg",
    "steps",
    "active_kcal",
    "intensity_minutes",
    "readiness_score",
    "readiness_level",
    "respiration_avg",
    "spo2_avg",
    "weight_kg",
)
_STORED_FIELDS = (*WELLNESS_FIELDS, "raw_json", "synced_at")


def _num(value: Any) -> float | None:
    # Garmin reports missing measurements as negative sentinels (e.g. stress -1/-2).
    if isinstance(value, bool) or not isinstance(value, int | float) or value < 0:
        return None
    return float(value)


def _first(*values: float | None) -> float | None:
    return next((v for v in values if v is not None), None)


def _latest_readiness(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list) and value:
        entries = [v for v in value if isinstance(v, dict)]
        return max(entries, key=lambda v: str(v.get("timestamp") or v.get("timestampLocal") or ""), default={})
    return {}


def normalize_wellness(day: str, raw: dict[str, Any]) -> dict[str, Any]:
    """Flatten the Garmin payloads of one day (summary, sleep, hrv, readiness, weight)."""
    summary = raw.get("summary") or {}
    sleep = raw.get("sleep") or {}
    sleep_dto = sleep.get("dailySleepDTO") or {}
    hrv = (raw.get("hrv") or {}).get("hrvSummary") or {}
    readiness = _latest_readiness(raw.get("readiness"))
    overall = (sleep_dto.get("sleepScores") or {}).get("overall") or {}
    moderate = _num(summary.get("moderateIntensityMinutes"))
    vigorous = _num(summary.get("vigorousIntensityMinutes"))
    return {
        "date": day,
        "sleep_seconds": _num(sleep_dto.get("sleepTimeSeconds")),
        "deep_sleep_seconds": _num(sleep_dto.get("deepSleepSeconds")),
        "rem_sleep_seconds": _num(sleep_dto.get("remSleepSeconds")),
        "light_sleep_seconds": _num(sleep_dto.get("lightSleepSeconds")),
        "awake_seconds": _num(sleep_dto.get("awakeSleepSeconds")),
        "sleep_score": _num(overall.get("value")),
        "hrv_last_night_ms": _first(_num(hrv.get("lastNightAvg")), _num(sleep.get("avgOvernightHrv"))),
        "hrv_weekly_avg_ms": _num(hrv.get("weeklyAvg")),
        "hrv_status": hrv.get("status") or sleep.get("hrvStatus"),
        "resting_hr": _first(_num(summary.get("restingHeartRate")), _num(sleep.get("restingHeartRate"))),
        "min_hr": _num(summary.get("minHeartRate")),
        "max_hr": _num(summary.get("maxHeartRate")),
        "body_battery_high": _num(summary.get("bodyBatteryHighestValue")),
        "body_battery_low": _num(summary.get("bodyBatteryLowestValue")),
        "body_battery_wake": _num(summary.get("bodyBatteryAtWakeTime")),
        "stress_avg": _num(summary.get("averageStressLevel")),
        "steps": _num(summary.get("totalSteps")),
        "active_kcal": _num(summary.get("activeKilocalories")),
        # Garmin counts vigorous minutes double toward the intensity goal.
        "intensity_minutes": None if moderate is None and vigorous is None else (moderate or 0) + 2 * (vigorous or 0),
        "readiness_score": _num(readiness.get("score")),
        "readiness_level": readiness.get("level"),
        "respiration_avg": _first(_num(summary.get("avgWakingRespirationValue")), _num(sleep_dto.get("averageRespirationValue"))),
        "spo2_avg": _num(summary.get("averageSpo2")),
        "weight_kg": _num(raw.get("weight_kg")),
        "raw_json": json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
    }


def upsert_wellness(db: Database, row: dict[str, Any]) -> None:
    columns = ", ".join(_STORED_FIELDS)
    values = ", ".join(f":{f}" for f in _STORED_FIELDS)
    updates = ", ".join(f"{f} = excluded.{f}" for f in _STORED_FIELDS if f != "date")
    with db.connect() as conn:
        conn.execute(
            f"INSERT INTO wellness_daily ({columns}) VALUES ({values}) ON CONFLICT(date) DO UPDATE SET {updates}",
            row,
        )


def wellness_rows(db: Database, *, today: date, days: int) -> list[dict[str, Any]]:
    """Rows of the last `days` days, newest first."""
    since = (today - timedelta(days=days - 1)).isoformat()
    with db.connect() as conn:
        rows = conn.execute(
            f"SELECT {', '.join(WELLNESS_FIELDS)} FROM wellness_daily WHERE date BETWEEN ? AND ? ORDER BY date DESC",
            [since, today.isoformat()],
        ).fetchall()
    return [dict(r) for r in rows]


def latest_weight(db: Database) -> tuple[str, float] | None:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT date, weight_kg FROM wellness_daily WHERE weight_kg IS NOT NULL ORDER BY date DESC LIMIT 1"
        ).fetchone()
    return (row["date"], row["weight_kg"]) if row else None


def _is_final(day: date, synced_at: str) -> bool:
    """A day is complete once it was re-read a few hours after midnight (late syncs from the watch)."""
    synced = datetime.fromisoformat(synced_at.replace("Z", "+00:00")).astimezone().replace(tzinfo=None)
    return synced >= datetime.combine(day + timedelta(days=1), datetime.min.time()) + timedelta(hours=3)


def sync_wellness(
    source: ActivitySource,
    db: Database,
    *,
    today: date,
    days: int,
    max_fetch: int | None,
    synced_at: str,
    pause_s: float = 0.0,
) -> int:
    """Refresh the days of the window that are missing or not final yet. Returns the days fetched."""
    with db.connect() as conn:
        known = {r["date"]: r["synced_at"] for r in conn.execute("SELECT date, synced_at FROM wellness_daily")}
    due = []
    for back in range(days):
        day = today - timedelta(days=back)
        synced = known.get(day.isoformat())
        if synced is None or not _is_final(day, synced):
            due.append(day)
    if max_fetch is not None:
        due = due[:max_fetch]
    if not due:
        return 0
    weights = source.fetch_weights((today - timedelta(days=days - 1)).isoformat(), today.isoformat())
    for i, day in enumerate(due):
        if i and pause_s:
            time.sleep(pause_s)
        raw = source.fetch_wellness(day.isoformat())
        raw["weight_kg"] = weights.get(day.isoformat())
        upsert_wellness(db, {**normalize_wellness(day.isoformat(), raw), "synced_at": synced_at})
    return len(due)
