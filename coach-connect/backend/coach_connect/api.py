"""HTTP API consumed by the mobile app."""

from __future__ import annotations

import secrets
import threading
import time
from collections import deque
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from . import __version__
from .backup import cloud_backup
from .coach import Coach, chat_history, clear_chat
from .config import Settings
from .db import Database
from .exercises import EXERCISES, GROUPS
from .garmin_auth import GarminLogin
from .normalize import SPORTS
from .plan import WORKOUTS
from .planner import plan_payload
from .progression import LoggedSet
from .sources import ActivitySource, GarminSource, SourceError, brief, build_source
from .sync import HISTORY_COMPLETE, LAST_SYNC_AT, SyncInProgress, Syncer
from .wellness import wellness_rows
from .workouts import create_workout, delete_workout, feed, feed_count, get_workout

# Online the access code is the only lock: past this many wrong codes in the window, wrong codes get 429.
WRONG_CODES_LIMIT = 30
WRONG_CODES_WINDOW_S = 600.0


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


class CoachStatus(BaseModel):
    mode: Literal["api", "ollama", "offline"]
    model: str | None


class Status(BaseModel):
    version: str
    mode: str
    garmin_ready: bool
    activity_count: int
    last_sync_at: str | None
    history_complete: bool
    coach: CoachStatus


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


class GarminLoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)


class GarminCodeIn(BaseModel):
    code: str = Field(min_length=4, max_length=12)


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


def create_app(
    settings: Settings | None = None, source: ActivitySource | None = None, coach: Coach | None = None
) -> FastAPI:
    settings = settings or Settings.from_env()
    if settings.web_dir and not settings.api_token:
        raise RuntimeError("Per servire il sito serve API_TOKEN (il codice di accesso): senza, chiunque vedrebbe i tuoi dati.")
    source = source or build_source(settings)
    coach = coach or Coach(settings)
    backup = cloud_backup(settings)
    if backup:
        backup.restore()
    db = Database(settings.db_path)
    syncer = Syncer(
        source,
        db,
        page_size=settings.sync_page_size,
        pause_s=0.5 if source.mode == "live" else 0.0,
        wellness_days=settings.wellness_days,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if backup:
            backup.flush()

    app = FastAPI(title="Coach Connect API", version=__version__, lifespan=lifespan)

    if backup:

        @app.middleware("http")
        async def save_changes(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
            response = await call_next(request)
            changed = request.method != "GET" and request.url.path.startswith("/api/")
            if changed and request.url.path != "/api/backup" and response.status_code < 400:
                backup.schedule()
            return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    wrong_codes: deque[float] = deque()
    wrong_codes_lock = threading.Lock()

    def require_token(authorization: str | None = Header(default=None)) -> None:
        if settings.api_token is None:
            return
        if authorization and secrets.compare_digest(authorization, f"Bearer {settings.api_token}"):
            return
        # A missing code is the app asking for it, not a guess.
        if authorization:
            now = time.monotonic()
            with wrong_codes_lock:
                while wrong_codes and now - wrong_codes[0] > WRONG_CODES_WINDOW_S:
                    wrong_codes.popleft()
                wrong_codes.append(now)
                too_many = len(wrong_codes) > WRONG_CODES_LIMIT
            if too_many:
                raise HTTPException(status_code=429, detail="Troppi codici sbagliati: riprova tra qualche minuto.")
        raise HTTPException(status_code=401, detail="Token API mancante o non valido")

    @app.exception_handler(SourceError)
    async def source_error(_: Request, exc: SourceError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "detail": str(exc)})

    @app.exception_handler(SyncInProgress)
    async def sync_in_progress(_: Request, exc: SyncInProgress) -> JSONResponse:
        return JSONResponse(status_code=409, content={"code": "sync_in_progress", "detail": str(exc)})

    protected = [Depends(require_token)]
    garmin_login = GarminLogin(settings.token_dir)
    web_dir = settings.web_dir.resolve() if settings.web_dir else None

    @app.get("/", include_in_schema=False, response_model=None)
    def root() -> Response:
        if web_dir:
            return FileResponse(web_dir / "index.html", headers={"Cache-Control": "no-cache"})
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
            coach=CoachStatus(**coach.status()),
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
        return {"messages": chat_history(db), "coach": coach.status()}

    @app.post("/api/chat", dependencies=protected)
    def send_chat(body: ChatIn) -> dict[str, Any]:
        messages = coach.reply(db, body.content.strip(), today=date.today())
        return {"messages": messages, "coach": coach.status()}

    @app.delete("/api/chat", status_code=204, dependencies=protected)
    def reset_chat() -> None:
        clear_chat(db)

    def garmin_connected() -> dict[str, str]:
        if isinstance(source, GarminSource):
            source.reload_tokens()
        return {"status": "connected"}

    @app.post("/api/garmin/login", dependencies=protected)
    def connect_garmin(body: GarminLoginIn) -> dict[str, str]:
        """Garmin login from the app; when it answers "needs_code", send the code to /api/garmin/code."""
        if source.mode != "live":
            raise HTTPException(status_code=409, detail="Con i dati demo non serve collegare Garmin.")
        if garmin_login.start(body.email.strip(), body.password) == "needs_code":
            return {"status": "needs_code"}
        return garmin_connected()

    @app.post("/api/garmin/code", dependencies=protected)
    def confirm_garmin_code(body: GarminCodeIn) -> dict[str, str]:
        garmin_login.finish(body.code.strip())
        return garmin_connected()

    @app.post("/api/backup", dependencies=protected, response_model=None)
    def save_backup() -> dict[str, str] | JSONResponse:
        """Save to the private dataset now (the deploy uses it to check that saving works)."""
        if backup is None:
            raise HTTPException(status_code=404, detail="Backup non configurato (HF_TOKEN e HF_DATA_REPO).")
        try:
            backup.upload()
        except Exception as exc:
            return JSONResponse(status_code=502, content={"code": "backup_failed", "detail": brief(exc)})
        return {"status": "saved"}

    if web_dir:

        @app.get("/{path:path}", include_in_schema=False)
        def web_app(path: str) -> FileResponse:
            if path.startswith("api/"):
                raise HTTPException(status_code=404, detail="Not Found")
            file = (web_dir / path).resolve()
            if file.is_file() and file.is_relative_to(web_dir):
                return FileResponse(file)
            # Routes of the single page app, like /scheda or /coach.
            return FileResponse(web_dir / "index.html", headers={"Cache-Control": "no-cache"})

    return app
