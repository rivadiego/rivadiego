"""HTTP API consumed by the mobile app."""

from __future__ import annotations

import secrets
from dataclasses import asdict
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from . import __version__
from .config import Settings
from .db import Database
from .normalize import SPORTS
from .sources import ActivitySource, SourceError, build_source
from .sync import HISTORY_COMPLETE, LAST_SYNC_AT, SyncInProgress, Syncer


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


class Status(BaseModel):
    version: str
    mode: str
    garmin_ready: bool
    activity_count: int
    last_sync_at: str | None
    history_complete: bool


class SyncResponse(BaseModel):
    mode: str
    new: int
    updated: int
    pages: int
    total: int
    last_sync_at: str
    history_complete: bool


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


def create_app(settings: Settings | None = None, source: ActivitySource | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    source = source or build_source(settings)
    db = Database(settings.db_path)
    syncer = Syncer(
        source,
        db,
        page_size=settings.sync_page_size,
        pause_s=0.5 if source.mode == "live" else 0.0,
    )

    app = FastAPI(title="Coach Connect API", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST"],
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

    @app.post("/api/sync", response_model=SyncResponse, dependencies=protected)
    def sync() -> SyncResponse:
        result = syncer.run(max_pages=settings.sync_max_pages)
        return SyncResponse(**asdict(result))

    return app
