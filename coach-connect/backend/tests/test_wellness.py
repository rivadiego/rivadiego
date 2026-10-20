from datetime import date, datetime, timezone

import pytest
from helpers import FakeSource

from coach_connect.db import Database
from coach_connect.wellness import latest_weight, normalize_wellness, sync_wellness, wellness_rows

GARMIN_DAY = {
    "summary": {
        "totalSteps": 11234,
        "activeKilocalories": 812,
        "restingHeartRate": 49,
        "minHeartRate": 45,
        "maxHeartRate": 171,
        "averageStressLevel": -1,
        "bodyBatteryHighestValue": 91,
        "bodyBatteryLowestValue": 22,
        "bodyBatteryAtWakeTime": 88,
        "moderateIntensityMinutes": 20,
        "vigorousIntensityMinutes": 15,
    },
    "sleep": {
        "dailySleepDTO": {
            "sleepTimeSeconds": 26640,
            "deepSleepSeconds": 5400,
            "remSleepSeconds": 5900,
            "lightSleepSeconds": 14400,
            "awakeSleepSeconds": 940,
            "sleepScores": {"overall": {"value": 84, "qualifierKey": "GOOD"}},
            "averageRespirationValue": 14.2,
        },
        "avgOvernightHrv": 57.0,
        "hrvStatus": "BALANCED",
    },
    "hrv": {"hrvSummary": {"lastNightAvg": 55, "weeklyAvg": 53, "status": "BALANCED"}},
    "readiness": [
        {"score": 61, "level": "MODERATE", "timestamp": "2026-10-20T05:10:00.0"},
        {"score": 78, "level": "HIGH", "timestamp": "2026-10-20T06:40:00.0"},
    ],
    "weight_kg": 70.4,
}


def test_normalize_garmin_day():
    row = normalize_wellness("2026-10-20", GARMIN_DAY)

    assert row["sleep_seconds"] == 26640 and row["sleep_score"] == 84
    assert (row["hrv_last_night_ms"], row["hrv_weekly_avg_ms"], row["hrv_status"]) == (55, 53, "BALANCED")
    assert row["resting_hr"] == 49
    assert (row["body_battery_wake"], row["body_battery_low"]) == (88, 22)
    assert row["stress_avg"] is None  # Garmin's "no data" sentinel
    assert row["intensity_minutes"] == 20 + 2 * 15
    assert (row["readiness_score"], row["readiness_level"]) == (78, "HIGH")
    assert row["respiration_avg"] == 14.2
    assert row["weight_kg"] == 70.4


def test_normalize_tolerates_missing_parts():
    row = normalize_wellness("2026-10-20", {"summary": None, "sleep": {"avgOvernightHrv": 50}, "hrv": None, "readiness": None})

    assert row["hrv_last_night_ms"] == 50
    assert row["sleep_seconds"] is None and row["readiness_score"] is None


class WellnessSource(FakeSource):
    def fetch_wellness(self, day):
        self.wellness_calls.append(day)
        return dict(GARMIN_DAY, weight_kg=None)

    def fetch_weights(self, start, end):
        return {"2026-10-19": 70.4}


@pytest.fixture
def db(tmp_path):
    return Database(tmp_path / "wellness.db")


def local_morning(hour):
    """`hour` o'clock on 2026-10-20 in the machine's timezone, as the UTC timestamp sync stores."""
    return datetime(2026, 10, 20, hour).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_sync_respects_budget_then_only_refreshes_unfinished_days(db):
    source = WellnessSource([])
    today = date(2026, 10, 20)

    first = sync_wellness(source, db, today=today, days=14, max_fetch=6, synced_at=local_morning(8))
    assert first == 6 and source.wellness_calls[0] == "2026-10-20"

    second = sync_wellness(source, db, today=today, days=14, max_fetch=None, synced_at=local_morning(9))
    # Days synced the morning of the 20th are final up to the 19th; today and the 8 missing days are fetched.
    assert second == 9

    source.wellness_calls.clear()
    third = sync_wellness(source, db, today=today, days=14, max_fetch=None, synced_at=local_morning(10))
    assert third == 1 and source.wellness_calls == ["2026-10-20"]

    assert len(wellness_rows(db, today=today, days=14)) == 14
    assert latest_weight(db) == ("2026-10-19", 70.4)
