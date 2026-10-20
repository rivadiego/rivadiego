import json

import pytest

from garmin_hub.normalize import normalize_activity, sport_for


@pytest.mark.parametrize(
    ("type_key", "sport"),
    [
        ("running", "run"),
        ("trail_running", "run"),
        ("treadmill_running", "run"),
        ("road_biking", "bike"),
        ("gravel_cycling", "bike"),
        ("indoor_cycling", "bike"),
        ("virtual_ride", "bike"),
        ("mountain_biking", "bike"),
        ("lap_swimming", "swim"),
        ("open_water_swimming", "swim"),
        ("walking", "walk"),
        ("hiking", "hike"),
        ("strength_training", "strength"),
        ("yoga", "mind_body"),
        ("hiit", "cardio"),
        ("indoor_rowing", "cardio"),
        ("rowing", "water"),
        ("resort_skiing_snowboarding_ws", "winter"),
        ("golf", "other"),
        (None, "other"),
    ],
)
def test_sport_for(type_key, sport):
    assert sport_for(type_key) == sport


def test_normalize_activity_maps_garmin_fields():
    raw = {
        "activityId": 21876543210,
        "activityName": "Milano Corsa",
        "activityType": {"typeId": 1, "typeKey": "running", "parentTypeId": 17},
        "startTimeLocal": "2026-10-19 07:12:03",
        "startTimeGMT": "2026-10-19 05:12:03",
        "distance": 10012.5,
        "duration": 3012.3,
        "movingDuration": 2990.0,
        "elevationGain": 45.0,
        "averageSpeed": 3.324,
        "averageHR": 148.0,
        "maxHR": 172,
        "calories": 650.0,
        "activityTrainingLoad": 120.5,
        "aerobicTrainingEffect": 3.2,
        "locationName": "Milano",
        "hasPolyline": True,
    }

    row = normalize_activity(raw)

    assert row["id"] == 21876543210
    assert (row["name"], row["type_key"], row["sport"]) == ("Milano Corsa", "running", "run")
    assert (row["start_time_local"], row["start_time_gmt"]) == ("2026-10-19 07:12:03", "2026-10-19 05:12:03")
    assert row["distance_m"] == 10012.5
    assert row["max_hr"] == 172.0
    assert row["training_load"] == 120.5
    assert row["location"] == "Milano"
    assert json.loads(row["raw_json"]) == raw


def test_normalize_activity_tolerates_missing_fields():
    row = normalize_activity(
        {
            "activityId": "42",
            "activityName": "  ",
            "activityType": {"typeKey": "strength_training"},
            "distance": None,
            "averageHR": True,
        }
    )

    assert row["id"] == 42
    assert row["name"] == "Strength training"
    assert row["distance_m"] is None
    assert row["avg_hr"] is None
    assert row["location"] is None
