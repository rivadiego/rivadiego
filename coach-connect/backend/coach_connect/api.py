"""HTTP API consumed by the mobile app."""

from __future__ import annotations

import secrets
from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from . import __version__
from .coach import chat_history, clear_chat, reply
from .config import Settings
from .db import Database
from .exercises import EXERCISES, GROUPS
from .normalize import SPORTS
from .plan import WORKOUTS
from .planner import plan_payload
from .progression import LoggedSet
from .sources import ActivitySource, SourceError, build_source
from .sync import HISTORY_COMPLETE, LAST_SYNC_AT, SyncInProgress, Syncer
from .wellness import wellness_rows
from .workouts import create_workout, delete_workout, feed, feed_count, get_workout


class Activity(BaseModel):
    id: int
    name: str
    sport: str
    type_key: str
    start_time_local: str | None
    start_time_utc: str | None
    duration_s: float | None
    moving_duration_s: float | None
    distance_m: float | None
    elevation_gain_m: float | None
    avg_speed_mps: float | None
    avg_hr: float | None
    max_hr: float | None
    calories: float | None
    training_load: float | None
    aerobic_te: float | None
    location: str | None


class ActivityPage(BaseModel):
    items: list[Activity]
    total: int
    limit: int
    offset: int
    mode: str
    last_sync_at: str | None


class FeedItem(BaseModel):
    key: str
    source: Literal["garmin", "manual"]
    id: int
    name: str
    sport: str
    type_key: str
    start_time_local: str | None
    start_time_utc: str | None
    duration_s: float | None
    distance_m: float | None
    elevation_gain_m: float | None
    avg_speed_mps: float | None
    avg_hr: float | None
    max_hr: float | None
    calories: float | None
    location: str | None
    plan_workout: str | None
    exercise_count: int | None
    set_count: int | None
    volume_kg: float | None
    garmin_linked: bool


class FeedPage(BaseModel):
    items: list[FeedItem]
    total: int
    limit: int
    offset: int
    mode: str
    last_sync_at: str | None


class Status(BaseModel):
    version: str
    mode: str
    garmin_ready: bool
    activity_count: int
    last_sync_at: str | None
    history_complete: bool
    coach_ai: bool


class SyncResponse(BaseModel):
    mode: str
    new: int
    updated: int
    pages: int
    total: int
    last_sync_at: str
    history_complete: bool
    wellness_days: int
    warning: str | None


class SetIn(BaseModel):
    weight_kg: float | None = Field(None, ge=0, le=500)
    reps: int | None = Field(None, ge=0, le=500)
    seconds: int | None = Field(None, ge=0, le=36_000)


class ExerciseIn(BaseModel):
    exercise_id: str
    sets: list[SetIn] = Field(min_length=1, max_length=20)


class WorkoutIn(BaseModel):
    name: str | None = Field(None, max_length=120)
    plan_workout: Literal["A", "B"] | None = None
    started_at: datetime | None = Field(None, description="ISO 8601 con fuso orario, es. 2026-10-20T07:10:00+02:00")
    duration_min: float | None = Field(None, ge=0, le=600)
    notes: str | None = Field(None, max_length=2000)
    exercises: list[ExerciseIn] = Field(min_length=1, max_length=30)


class ChatIn(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


def _iso(value: str | None, *, utc: bool = False) -> str | None:
    """Garmin's "YYYY-MM-DD HH:MM:SS" -> ISO 8601, with a trailing "Z" for UTC times."""
    if not value:
        return None
    iso = value.replace(" ", "T")
    return f"{iso}Z" if utc and not iso.endswith("Z") else iso


def _activity(row: dict[str, Any]) -> Activity:
    data = dict(row)
    data["start_time_local"] = _iso(data.pop("start_time_local"))
    data["start_time_utc"] = _iso(data.pop("start_time_gmt"), utc=True)
    return Activity(**data)


def _feed_item(row: dict[str, Any]) -> FeedItem:
    data = dict(row)
    data["key"] = f"{data['source']}:{data['id']}"
    data["start_time_local"] = _iso(data.pop("start_time_local"))
    data["start_time_utc"] = _iso(data.pop("start_time_gmt"), utc=True)
    data["garmin_linked"] = bool(data["garmin_linked"])
    return FeedItem(**data)


def _workout_response(workout: dict[str, Any]) -> dict[str, Any]:
    data = dict(workout)
    data["start_time_local"] = _iso(data["start_time_local"])
    data["start_time_utc"] = _iso(data.pop("start_time_gmt"), utc=True)
    return data


def create_app(settings: Settings | None = None, source: ActivitySource | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    source = source or build_source(settings)
    db = Database(settings.db_path)
    syncer = Syncer(
        source,
        db,
        page_size=settings.sync_page_size,
        pause_s=0.5 if source.mode == "live" else 0.0,
        wellness_days=settings.wellness_days,
    )

    app = FastAPI(title="Coach Connect API", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    def require_token(authorization: str | None = Header(default=None)) -> None:
        if settings.api_token is None:
            return
        expected = f"Bearer {settings.api_token}"
        if not authorization or not secrets.compare_digest(authorization, expected):
            raise HTTPException(status_code=401, detail="Token API mancante o non valido")

    @app.exception_handler(SourceError)
    async def source_error(_: Request, exc: SourceError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "detail": str(exc)})

    @app.exception_handler(SyncInProgress)
    async def sync_in_progress(_: Request, exc: SyncInProgress) -> JSONResponse:
        return JSONResponse(status_code=409, content={"code": "sync_in_progress", "detail": str(exc)})

    protected = [Depends(require_token)]

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse("/docs")

    @app.get("/api/status", response_model=Status, dependencies=protected)
    def status() -> Status:
        return Status(
            version=__version__,
            mode=source.mode,
            garmin_ready=source.is_ready(),
            activity_count=db.count_activities(),
            last_sync_at=db.get_meta(LAST_SYNC_AT),
            history_complete=db.get_meta(HISTORY_COMPLETE) == "1",
            coach_ai=settings.llm_configured,
        )

    @app.get("/api/activities", response_model=ActivityPage, dependencies=protected)
    def activities(
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
        sport: str | None = Query(None, description=f"Uno tra: {', '.join(SPORTS)}"),
    ) -> ActivityPage:
        rows = db.list_activities(limit=limit, offset=offset, sport=sport)
        return ActivityPage(
            items=[_activity(r) for r in rows],
            total=db.count_activities(sport),
            limit=limit,
            offset=offset,
            mode=source.mode,
            last_sync_at=db.get_meta(LAST_SYNC_AT),
        )

    @app.get("/api/feed", response_model=FeedPage, dependencies=protected)
    def activity_feed(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)) -> FeedPage:
        """Garmin activities and logged gym sessions, newest first."""
        return FeedPage(
            items=[_feed_item(r) for r in feed(db, limit=limit, offset=offset)],
            total=feed_count(db),
            limit=limit,
            offset=offset,
            mode=source.mode,
            last_sync_at=db.get_meta(LAST_SYNC_AT),
        )

    @app.post("/api/sync", response_model=SyncResponse, dependencies=protected)
    def sync() -> SyncResponse:
        result = syncer.run(max_pages=settings.sync_max_pages, max_wellness_days=settings.wellness_max_days_per_sync)
        return SyncResponse(**asdict(result))

    @app.get("/api/exercises", dependencies=protected)
    def exercises() -> dict[str, Any]:
        return {"groups": list(GROUPS), "exercises": [e.to_dict() for e in EXERCISES.values()]}

    @app.get("/api/plan", dependencies=protected)
    def plan() -> dict[str, Any]:
        return plan_payload(db, settings, date.today())

    @app.post("/api/workouts", status_code=201, dependencies=protected)
    def log_workout(body: WorkoutIn) -> dict[str, Any]:
        unknown = [e.exercise_id for e in body.exercises if e.exercise_id not in EXERCISES]
        if unknown:
            raise HTTPException(status_code=422, detail=f"Esercizi sconosciuti: {', '.join(unknown)}")
        started = body.started_at or datetime.now().astimezone()
        if started.tzinfo is None:
            started = started.astimezone()
        workout_id = create_workout(
            db,
            name=body.name or (WORKOUTS[body.plan_workout]["title"] if body.plan_workout else "Allenamento in palestra"),
            plan_workout=body.plan_workout,
            # The wall-clock time where the workout happened, like Garmin's startTimeLocal.
            start_local=started.replace(tzinfo=None),
            start_utc=started.astimezone(timezone.utc).replace(tzinfo=None),
            duration_s=body.duration_min * 60 if body.duration_min else None,
            notes=body.notes,
            exercises=[
                (e.exercise_id, [LoggedSet(s.weight_kg, s.reps, s.seconds) for s in e.sets]) for e in body.exercises
            ],
        )
        workout = get_workout(db, workout_id)
        assert workout is not None
        return _workout_response(workout)

    @app.get("/api/workouts/{workout_id}", dependencies=protected)
    def read_workout(workout_id: int) -> dict[str, Any]:
        workout = get_workout(db, workout_id)
        if workout is None:
            raise HTTPException(status_code=404, detail="Allenamento non trovato")
        return _workout_response(workout)

    @app.delete("/api/workouts/{workout_id}", status_code=204, dependencies=protected)
    def remove_workout(workout_id: int) -> None:
        if not delete_workout(db, workout_id):
            raise HTTPException(status_code=404, detail="Allenamento non trovato")

    @app.get("/api/wellness", dependencies=protected)
    def wellness(days: int = Query(14, ge=1, le=90)) -> dict[str, Any]:
        return {"days": wellness_rows(db, today=date.today(), days=days)}

    @app.get("/api/chat", dependencies=protected)
    def chat() -> dict[str, Any]:
        return {"messages": chat_history(db), "coach_ai": settings.llm_configured}

    @app.post("/api/chat", dependencies=protected)
    def send_chat(body: ChatIn) -> dict[str, Any]:
        messages = reply(db, settings, body.content.strip(), today=date.today())
        return {"messages": messages, "coach_ai": settings.llm_configured}

    @app.delete("/api/chat", status_code=204, dependencies=protected)
    def reset_chat() -> None:
        clear_chat(db)

    return app
