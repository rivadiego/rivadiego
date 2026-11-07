"""MCP server: chat with your Coach Connect data from Cursor (or any MCP client)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from mcp.server.mcpserver import MCPServer

from .coach import build_snapshot, system_prompt
from .config import Settings
from .db import Database
from .planner import plan_payload
from .wellness import wellness_rows
from .workouts import feed
from .workouts import get_workout as load_workout

INSTRUCTIONS = (
    "Training data of a hybrid athlete (gym + running) from Coach Connect: plan, logged gym workouts, Garmin "
    "activities and daily vital signs. To act as their personal trainer, call get_coach_context first and answer "
    "in Italian."
)


def build_server(settings: Settings | None = None) -> MCPServer:
    settings = settings or Settings.from_env()
    db = Database(settings.db_path)
    server = MCPServer("coach-connect", instructions=INSTRUCTIONS)

    @server.tool()
    def get_coach_context() -> str:
        """Everything a personal trainer needs, in Italian: plan rules, next workout with the loads computed by
        the plan's progression rules, the last 14 days of vital signs (sleep, HRV, Body Battery, readiness),
        Garmin activities and logged gym sets."""
        return system_prompt(build_snapshot(db, settings, date.today()))

    @server.tool()
    def get_next_workout() -> dict[str, Any]:
        """The next gym workout (A or B) with the suggested loads for every exercise and the last session's sets."""
        plan = plan_payload(db, settings, date.today())
        workout = plan["workouts"][plan["next_workout"]]
        return {
            "workout": workout["title"],
            "last_workout": plan["last_workout"],
            "exercises": [
                {
                    "name": e["name"],
                    "scheme": e["scheme_label"],
                    "suggested_sets": e["suggestion"]["sets"],
                    "why": e["suggestion"]["message"],
                    "last_sets": e["last"],
                    "warmup": e["suggestion"]["warmup"],
                }
                for e in workout["exercises"]
            ],
        }

    @server.tool()
    def get_vital_signs(days: int = 14) -> list[dict[str, Any]]:
        """Daily vital signs from Garmin, newest first: sleep, HRV, resting heart rate, Body Battery, stress,
        steps, intensity minutes, readiness, weight."""
        return wellness_rows(db, today=date.today(), days=max(1, min(days, 90)))

    @server.tool()
    def get_activities(days: int = 14) -> list[dict[str, Any]]:
        """Garmin activities and logged gym workouts of the last `days` days, newest first."""
        since = (date.today() - timedelta(days=max(1, min(days, 365)) - 1)).isoformat()
        return feed(db, limit=500, since_local=since)

    @server.tool()
    def get_workout(workout_id: int) -> dict[str, Any]:
        """A logged gym workout with every set (kg × reps, or seconds)."""
        return load_workout(db, workout_id) or {"error": f"Nessun allenamento con id {workout_id}"}

    return server


def run() -> None:
    build_server().run("stdio")
