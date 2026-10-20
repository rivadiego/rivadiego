"""Where data comes from: the real Garmin Connect account or a demo generator."""

from __future__ import annotations

import random
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, NamedTuple, Protocol

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectNotFoundError,
    GarminConnectTooManyRequestsError,
)

from .config import Settings
from .db import Database

TOKEN_FILE = "garmin_tokens.json"


def brief(exc: Exception, limit: int = 140) -> str:
    """The start of a library error, short enough for a phone screen."""
    text = " ".join(str(exc).split())
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


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

    def fetch_wellness(self, day: str) -> dict[str, Any]:
        """Raw daily payloads keyed "summary", "sleep", "hrv" and "readiness" (missing parts may be None)."""
        ...

    def fetch_weights(self, start: str, end: str) -> dict[str, float]:
        """Body weight in kg by date, for the weigh-ins between two dates."""
        ...

    def after_sync(self, db: Database) -> None: ...


class GarminSource:
    """Garmin Connect account, authenticated with the tokens saved at login (from the app or the command line)."""

    mode = "live"

    def __init__(self, token_dir: Path) -> None:
        self.token_dir = token_dir
        self._client: Garmin | None = None

    def is_ready(self) -> bool:
        return (self.token_dir / TOKEN_FILE).is_file()

    def reload_tokens(self) -> None:
        """Use the tokens of a new login from the next request on."""
        self._client = None

    def begin_sync(self) -> None:
        return None

    def after_sync(self, db: Database) -> None:
        return None

    def fetch_activities(self, start: int, limit: int) -> list[dict[str, Any]]:
        with self._errors():
            activities = self._get_client().get_activities(start, limit)
        return activities if isinstance(activities, list) else []

    def fetch_wellness(self, day: str) -> dict[str, Any]:
        with self._errors():
            client = self._get_client()
            calls: dict[str, Callable[[], Any]] = {
                "summary": lambda: client.get_user_summary(day),
                "sleep": lambda: client.get_sleep_data(day),
                "hrv": lambda: client.get_hrv_data(day),
                "readiness": lambda: client.get_training_readiness(day),
            }
            raw: dict[str, Any] = {}
            for key, call in calls.items():
                try:
                    raw[key] = call()
                except GarminConnectNotFoundError:
                    # Not every watch records every metric (HRV, readiness…).
                    raw[key] = None
        return raw

    def fetch_weights(self, start: str, end: str) -> dict[str, float]:
        with self._errors():
            try:
                data = self._get_client().get_body_composition(start, end) or {}
            except GarminConnectNotFoundError:
                return {}
        weights = {}
        for item in data.get("dateWeightList") or []:
            grams = item.get("weight")
            if item.get("calendarDate") and isinstance(grams, int | float) and grams > 0:
                weights[item["calendarDate"]] = round(grams / 1000, 2)
        return weights

    @contextmanager
    def _errors(self) -> Iterator[None]:
        try:
            yield
        except GarminConnectAuthenticationError as exc:
            self._client = None
            raise GarminNotAuthenticated(
                "Sessione Garmin non valida o scaduta: collegati di nuovo con «Collega Garmin» "
                "(o con `python -m coach_connect login` sul computer che fa da server)."
            ) from exc
        except GarminConnectTooManyRequestsError as exc:
            raise GarminRateLimited(
                "Garmin sta limitando le richieste: riprova tra qualche minuto."
            ) from exc
        except GarminConnectConnectionError as exc:
            raise GarminUnavailable(f"Garmin Connect non raggiungibile: {brief(exc)}") from exc

    def _get_client(self) -> Garmin:
        if self._client is None:
            if not self.is_ready():
                raise GarminNotAuthenticated(
                    "Garmin non ancora collegato: tocca «Collega Garmin» "
                    "(o esegui `python -m coach_connect login` sul computer che fa da server)."
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


DEMO_BODYWEIGHT_KG = 70.0


class DemoSource:
    """Generates realistic fake data so the app can be tried without a Garmin account.

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

    def after_sync(self, db: Database) -> None:
        from .workouts import seed_demo_workouts

        seed_demo_workouts(db, bodyweight=DEMO_BODYWEIGHT_KG)

    def fetch_wellness(self, day: str) -> dict[str, Any]:
        current = date.fromisoformat(day)
        rng = random.Random(current.toordinal())
        hard_day_before = _planned_kind(current - timedelta(days=1)) in {"quality_run", "long_run"}
        hrv = rng.uniform(48, 64) - (6 if hard_day_before else 0)
        sleep_s = rng.uniform(6.0, 8.1) * 3600
        sleep_score = round(min(95, 40 + sleep_s / 3600 * 6 + rng.uniform(-6, 6)))
        resting_hr = round(rng.uniform(47, 52) + (2 if hard_day_before else 0))
        wake_battery = round(min(100, 35 + sleep_score * 0.6 + rng.uniform(-8, 8)))
        readiness = round(max(15, min(98, wake_battery * 0.7 + (hrv - 45) * 1.2 + rng.uniform(-5, 5))))
        day_share = min(1.0, datetime.now().hour / 22) if current == date.today() else 1.0
        status = "BALANCED" if hrv >= 50 else "UNBALANCED"
        level = "HIGH" if readiness >= 75 else "MODERATE" if readiness >= 50 else "LOW" if readiness >= 25 else "POOR"
        return {
            "summary": {
                "totalSteps": round(rng.uniform(7000, 14000) * day_share),
                "activeKilocalories": round(rng.uniform(450, 1100) * day_share),
                "restingHeartRate": resting_hr,
                "minHeartRate": resting_hr - 3,
                "maxHeartRate": round(rng.uniform(150, 178)),
                "averageStressLevel": round(rng.uniform(18, 38)),
                "bodyBatteryHighestValue": wake_battery,
                "bodyBatteryLowestValue": round(max(5, wake_battery - rng.uniform(40, 70) * day_share)),
                "bodyBatteryAtWakeTime": wake_battery,
                "moderateIntensityMinutes": round(rng.uniform(10, 50) * day_share),
                "vigorousIntensityMinutes": round(rng.uniform(0, 40) * day_share),
                "avgWakingRespirationValue": round(rng.uniform(13, 16), 1),
                "averageSpo2": round(rng.uniform(94, 98)),
            },
            "sleep": {
                "dailySleepDTO": {
                    "sleepTimeSeconds": round(sleep_s),
                    "deepSleepSeconds": round(sleep_s * rng.uniform(0.15, 0.22)),
                    "remSleepSeconds": round(sleep_s * rng.uniform(0.18, 0.25)),
                    "lightSleepSeconds": round(sleep_s * 0.55),
                    "awakeSleepSeconds": round(rng.uniform(300, 1800)),
                    "sleepScores": {"overall": {"value": sleep_score}},
                },
                "avgOvernightHrv": round(hrv),
                "hrvStatus": status,
                "restingHeartRate": resting_hr,
            },
            "hrv": {"hrvSummary": {"lastNightAvg": round(hrv), "weeklyAvg": round(rng.uniform(52, 57)), "status": status}},
            "readiness": [{"score": readiness, "level": level, "timestamp": f"{day}T06:30:00.0"}],
        }

    def fetch_weights(self, start: str, end: str) -> dict[str, float]:
        weights = {}
        day = date.fromisoformat(start)
        while day <= date.fromisoformat(end):
            if day.weekday() == 0:
                rng = random.Random(day.toordinal() + 1)
                weeks = (day - date(2026, 1, 5)).days // 7
                weights[day.isoformat()] = round(DEMO_BODYWEIGHT_KG - 1 + 0.03 * weeks + rng.uniform(-0.3, 0.3), 1)
            day += timedelta(days=1)
        return weights

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
