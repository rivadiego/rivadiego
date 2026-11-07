"""Turn raw Garmin Connect activity payloads into flat rows."""

from __future__ import annotations

import json
from typing import Any

SPORTS = (
    "run",
    "bike",
    "swim",
    "walk",
    "hike",
    "strength",
    "cardio",
    "mind_body",
    "winter",
    "water",
    "other",
)

# Checked in order: the first keyword contained in Garmin's typeKey wins.
_SPORT_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("swim", "swim"),
    ("run", "run"),
    ("indoor_row", "cardio"),
    ("cycl", "bike"),
    ("bik", "bike"),
    ("ride", "bike"),
    ("hik", "hike"),
    ("mountaineering", "hike"),
    ("walk", "walk"),
    ("strength", "strength"),
    ("yoga", "mind_body"),
    ("pilates", "mind_body"),
    ("breath", "mind_body"),
    ("meditation", "mind_body"),
    ("ski", "winter"),
    ("snow", "winter"),
    ("row", "water"),
    ("paddl", "water"),
    ("kayak", "water"),
    ("surf", "water"),
    ("sail", "water"),
    ("cardio", "cardio"),
    ("hiit", "cardio"),
    ("elliptical", "cardio"),
    ("stair", "cardio"),
    ("floor_climbing", "cardio"),
    ("jump_rope", "cardio"),
)


def sport_for(type_key: str | None) -> str:
    key = (type_key or "").lower()
    for keyword, sport in _SPORT_KEYWORDS:
        if keyword in key:
            return sport
    return "other"


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def _pretty(type_key: str) -> str:
    return type_key.replace("_", " ").strip().capitalize() or "Attività"


def normalize_activity(raw: dict[str, Any]) -> dict[str, Any]:
    type_key = (raw.get("activityType") or {}).get("typeKey") or "other"
    return {
        "id": int(raw["activityId"]),
        "name": (raw.get("activityName") or "").strip() or _pretty(type_key),
        "type_key": type_key,
        "sport": sport_for(type_key),
        "start_time_local": raw.get("startTimeLocal"),
        "start_time_gmt": raw.get("startTimeGMT"),
        "duration_s": _number(raw.get("duration")),
        "moving_duration_s": _number(raw.get("movingDuration")),
        "distance_m": _number(raw.get("distance")),
        "elevation_gain_m": _number(raw.get("elevationGain")),
        "avg_speed_mps": _number(raw.get("averageSpeed")),
        "avg_hr": _number(raw.get("averageHR")),
        "max_hr": _number(raw.get("maxHR")),
        "calories": _number(raw.get("calories")),
        "training_load": _number(raw.get("activityTrainingLoad")),
        "aerobic_te": _number(raw.get("aerobicTrainingEffect")),
        "location": raw.get("locationName"),
        # The full payload is kept so future features can use any Garmin field without re-syncing.
        "raw_json": json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
    }
