from __future__ import annotations

import urllib.error
from datetime import datetime, timedelta
from typing import Any

from coach_connect.coach import Coach, OllamaClient
from coach_connect.config import Settings

NEWEST = datetime(2026, 10, 20, 7, 0, 0)


def no_ollama(url: str, timeout: float) -> dict[str, Any]:
    raise urllib.error.URLError("connection refused")


def offline_coach(settings: Settings) -> Coach:
    """A coach that never reaches a real Ollama running on the developer's machine."""
    return Coach(settings, ollama=OllamaClient(settings, get=no_ollama))


def make_raw(
    index: int,
    *,
    activity_id: int | None = None,
    type_key: str = "running",
    name: str | None = None,
) -> dict[str, Any]:
    """Garmin-like activity payload; index 0 is the newest, negative indexes are newer still."""
    start = NEWEST - timedelta(hours=8 * index)
    return {
        "activityId": activity_id if activity_id is not None else 1_000_000 + index,
        "activityName": name if name is not None else f"Attività {index}",
        "activityType": {"typeKey": type_key, "typeId": 1},
        "startTimeLocal": start.strftime("%Y-%m-%d %H:%M:%S"),
        "startTimeGMT": (start - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "distance": 10_000.0,
        "duration": 3_000.0,
        "averageSpeed": 3.33,
        "averageHR": 150.0,
    }


class FakeSource:
    mode = "test"

    def __init__(self, activities: list[dict[str, Any]]) -> None:
        self.activities = activities
        self.calls: list[tuple[int, int]] = []
        self.wellness_calls: list[str] = []

    def is_ready(self) -> bool:
        return True

    def begin_sync(self) -> None:
        return None

    def after_sync(self, db: Any) -> None:
        return None

    def fetch_activities(self, start: int, limit: int) -> list[dict[str, Any]]:
        self.calls.append((start, limit))
        return [dict(a) for a in self.activities[start : start + limit]]

    def fetch_wellness(self, day: str) -> dict[str, Any]:
        self.wellness_calls.append(day)
        return {}

    def fetch_weights(self, start: str, end: str) -> dict[str, float]:
        return {}
