"""SQLite storage for synced activities."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS activities (
    id                INTEGER PRIMARY KEY,
    name              TEXT NOT NULL,
    type_key          TEXT NOT NULL,
    sport             TEXT NOT NULL,
    start_time_local  TEXT,
    start_time_gmt    TEXT,
    duration_s        REAL,
    moving_duration_s REAL,
    distance_m        REAL,
    elevation_gain_m  REAL,
    avg_speed_mps     REAL,
    avg_hr            REAL,
    max_hr            REAL,
    calories          REAL,
    training_load     REAL,
    aerobic_te        REAL,
    location          TEXT,
    raw_json          TEXT NOT NULL,
    synced_at         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_activities_start ON activities (start_time_gmt DESC);
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""

ACTIVITY_FIELDS = (
    "id",
    "name",
    "type_key",
    "sport",
    "start_time_local",
    "start_time_gmt",
    "duration_s",
    "moving_duration_s",
    "distance_m",
    "elevation_gain_m",
    "avg_speed_mps",
    "avg_hr",
    "max_hr",
    "calories",
    "training_load",
    "aerobic_te",
    "location",
    "raw_json",
    "synced_at",
)
SUMMARY_FIELDS = tuple(f for f in ACTIVITY_FIELDS if f not in {"raw_json", "synced_at"})


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def upsert_activities(self, rows: list[dict[str, Any]]) -> tuple[int, int]:
        """Insert new activities and rewrite changed ones. Returns (new, updated)."""
        if not rows:
            return 0, 0
        ids = [row["id"] for row in rows]
        columns = ", ".join(ACTIVITY_FIELDS)
        values = ", ".join(f":{f}" for f in ACTIVITY_FIELDS)
        updates = ", ".join(f"{f} = excluded.{f}" for f in ACTIVITY_FIELDS if f != "id")
        with self._connect() as conn:
            existing = {
                r["id"]: r["raw_json"]
                for r in conn.execute(
                    f"SELECT id, raw_json FROM activities WHERE id IN ({', '.join('?' * len(ids))})",
                    ids,
                )
            }
            changed = [row for row in rows if existing.get(row["id"]) != row["raw_json"]]
            conn.executemany(
                f"INSERT INTO activities ({columns}) VALUES ({values}) "
                f"ON CONFLICT(id) DO UPDATE SET {updates}",
                changed,
            )
        new = sum(1 for row in changed if row["id"] not in existing)
        return new, len(changed) - new

    def list_activities(
        self, *, limit: int, offset: int = 0, sport: str | None = None
    ) -> list[dict[str, Any]]:
        where, params = ("WHERE sport = ?", [sport]) if sport else ("", [])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT {', '.join(SUMMARY_FIELDS)} FROM activities {where} "
                "ORDER BY start_time_gmt DESC, id DESC LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()
        return [dict(r) for r in rows]

    def count_activities(self, sport: str | None = None) -> int:
        where, params = ("WHERE sport = ?", [sport]) if sport else ("", [])
        with self._connect() as conn:
            return conn.execute(f"SELECT COUNT(*) FROM activities {where}", params).fetchone()[0]

    def get_meta(self, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM meta WHERE key = ?", [key]).fetchone()
        return row["value"] if row else None

    def set_meta(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                [key, value],
            )
