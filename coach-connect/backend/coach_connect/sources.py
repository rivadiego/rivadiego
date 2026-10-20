"""Where activities come from: the real Garmin Connect account or a demo generator."""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, NamedTuple, Protocol

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

from .config import Settings

TOKEN_FILE = "garmin_tokens.json"


class SourceError(Exception):
    """An error the API reports to the app with a stable code."""

    status_code = 502
    code = "source_error"


class GarminNotAuthenticated(SourceError):
    status_code = 503
    code = "garmin_not_authenticated"


class GarminRateLimited(SourceError):
    status_code = 429
    code = "garmin_rate_limited"


class GarminUnavailable(SourceError):
    status_code = 502
    code = "garmin_unavailable"


class ActivitySource(Protocol):
    mode: str

    def is_ready(self) -> bool: ...

    def begin_sync(self) -> None: ...

    def fetch_activities(self, start: int, limit: int) -> list[dict[str, Any]]:
        """Return a page of raw Garmin activity payloads, newest first."""
        ...


class GarminSource:
    """Garmin Connect account, authenticated with the tokens saved by `python -m coach_connect login`."""

    mode = "live"

    def __init__(self, token_dir: Path) -> None:
        self.token_dir = token_dir
        self._client: Garmin | None = None

    def is_ready(self) -> bool:
        return (self.token_dir / TOKEN_FILE).is_file()

    def begin_sync(self) -> None:
        return None

    def fetch_activities(self, start: int, limit: int) -> list[dict[str, Any]]:
        try:
            activities = self._get_client().get_activities(start, limit)
        except GarminConnectAuthenticationError as exc:
            self._client = None
            raise GarminNotAuthenticated(
                "Sessione Garmin non valida o scaduta: esegui di nuovo "
                "`python -m coach_connect login` sul computer che fa da server."
            ) from exc
        except GarminConnectTooManyRequestsError as exc:
            raise GarminRateLimited(
                "Garmin sta limitando le richieste: riprova tra qualche minuto."
            ) from exc
        except GarminConnectConnectionError as exc:
            raise GarminUnavailable(f"Garmin Connect non raggiungibile: {exc}") from exc
        return activities if isinstance(activities, list) else []

    def _get_client(self) -> Garmin:
        if self._client is None:
            if not self.is_ready():
                raise GarminNotAuthenticated(
                    "Garmin non ancora collegato: esegui `python -m coach_connect login` "
                    "sul computer che fa da server."
                )
            client = Garmin()
            # Loads the saved tokens; the library refreshes them and writes them back on its own.
            client.login(str(self.token_dir))
            self._client = client
        return self._client


class _DemoKind(NamedTuple):
    type_key: str
    names: tuple[str, ...]
    location: str
    amount: tuple[float, float]  # distance in km, or duration in minutes when speed is (0, 0)
    speed: tuple[float, float]  # km/h
    hr: tuple[int, int]
    elevation: tuple[int, int]  # m
    kcal_per_hour: int


_DEMO_KINDS: dict[str, _DemoKind] = {
    "push": _DemoKind("strength_training", ("Workout A · Push",), "Palestra", (50, 62), (0, 0), (98, 122), (0, 0), 360),
    "pull": _DemoKind("strength_training", ("Workout B · Pull",), "Palestra", (50, 62), (0, 0), (100, 124), (0, 0), 370),
    "quality_run": _DemoKind(
        "running", ("Ripetute 6×1000", "Tempo run", "Fartlek 10×1'"), "Milano", (7, 10), (12.2, 13.8), (152, 166), (10, 40), 780
    ),
    "long_run": _DemoKind("running", ("Lungo domenicale",), "Parco di Monza", (12, 18), (10.4, 11.6), (140, 152), (40, 140), 720),
    "walk": _DemoKind("walking", ("Camminata",), "Milano", (3, 7), (4.6, 5.6), (88, 106), (5, 40), 260),
}


def _planned_kind(day: date) -> str | None:
    """Hybrid athlete week: gym Mon/Wed/Fri alternating A (push) and B (pull), quality run Tue, long run Sun."""
    a_first = day.isocalendar().week % 2 == 0
    match day.weekday():
        case 0 | 4:
            return "push" if a_first else "pull"
        case 2:
            return "pull" if a_first else "push"
        case 1:
            return "quality_run"
        case 6:
            return "long_run"
        case _:
            return None


class DemoSource:
    """Generates realistic fake activities so the app can be tried without a Garmin account.

    The week mirrors a 3 gym + 2 runs hybrid plan. History is derived from today's date, so
    restarts on the same day return identical data. Every sync after the first one "records"
    a fresh activity, to show the refresh flow.
    """

    mode = "demo"

    def __init__(self, days: int = 150, seed: int = 7) -> None:
        self._rng = random.Random(seed)
        self._utc_offset = datetime.now().astimezone().utcoffset() or timedelta()
        self._activities = self._history(date.today(), days)
        self._syncs = 0

    def is_ready(self) -> bool:
        return True

    def begin_sync(self) -> None:
        self._syncs += 1
        if self._syncs == 1:
            return
        now = datetime.now().replace(microsecond=0)
        done_today = any(a["startTimeLocal"].startswith(now.strftime("%Y-%m-%d")) for a in self._activities)
        kind = "walk" if done_today else _planned_kind(now.date()) or "walk"
        activity = self._activity(int(now.timestamp()), kind, now)
        # Make it end a few minutes ago, as if the watch had just synced it.
        start = now - timedelta(seconds=activity["duration"], minutes=self._rng.randint(3, 15))
        activity["startTimeLocal"] = start.strftime("%Y-%m-%d %H:%M:%S")
        activity["startTimeGMT"] = (start - self._utc_offset).strftime("%Y-%m-%d %H:%M:%S")
        self._activities.insert(0, activity)

    def fetch_activities(self, start: int, limit: int) -> list[dict[str, Any]]:
        return [dict(a) for a in self._activities[start : start + limit]]

    def _history(self, today: date, days: int) -> list[dict[str, Any]]:
        now = datetime.now()
        activities = []
        for back in range(days):
            day = today - timedelta(days=back)
            kind = _planned_kind(day)
            if kind is None:
                kind = "walk" if self._rng.random() < 0.25 else None
            elif self._rng.random() < 0.1:
                kind = None  # a missed session now and then
            if kind is None:
                continue
            hour, minute = (8, self._rng.randint(0, 50)) if kind == "long_run" else (6, self._rng.randint(20, 59))
            if kind == "walk":
                hour = self._rng.choice((12, 18, 19))
            start = datetime(day.year, day.month, day.day, hour, minute, self._rng.randint(0, 59))
            activity = self._activity(int(day.strftime("%Y%m%d")) * 10, kind, start)
            if start + timedelta(seconds=activity["duration"]) < now:
                activities.append(activity)
        return activities

    def _activity(self, activity_id: int, kind: str, start: datetime) -> dict[str, Any]:
        spec = _DEMO_KINDS[kind]
        rng = self._rng
        if spec.speed == (0, 0):
            distance_m, duration_s, avg_speed = 0.0, rng.uniform(*spec.amount) * 60, 0.0
        else:
            distance_m = rng.uniform(*spec.amount) * 1000
            avg_speed = rng.uniform(*spec.speed) / 3.6
            duration_s = distance_m / avg_speed
        avg_hr = rng.randint(*spec.hr)
        hours = duration_s / 3600
        return {
            "activityId": activity_id,
            "activityName": rng.choice(spec.names),
            "activityType": {"typeKey": spec.type_key},
            "startTimeLocal": start.strftime("%Y-%m-%d %H:%M:%S"),
            "startTimeGMT": (start - self._utc_offset).strftime("%Y-%m-%d %H:%M:%S"),
            "distance": round(distance_m, 1),
            "duration": round(duration_s, 1),
            "movingDuration": round(duration_s * rng.uniform(0.93, 0.99), 1),
            "elevationGain": float(rng.randint(*spec.elevation)),
            "averageSpeed": round(avg_speed, 3),
            "averageHR": float(avg_hr),
            "maxHR": float(avg_hr + rng.randint(12, 26)),
            "calories": round(spec.kcal_per_hour * hours),
            "activityTrainingLoad": round(hours * (avg_hr - 60) * rng.uniform(0.9, 1.2), 1),
            "aerobicTrainingEffect": round(min(5.0, 1.2 + hours * 1.8 + (avg_hr - 120) / 40), 1),
            "locationName": spec.location,
        }


def build_source(settings: Settings) -> ActivitySource:
    return DemoSource() if settings.demo else GarminSource(settings.token_dir)
