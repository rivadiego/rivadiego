import asyncio
import json

import pytest

from coach_connect.config import Settings
from coach_connect.db import Database
from coach_connect.mcp_server import build_server
from coach_connect.sources import DemoSource
from coach_connect.sync import Syncer


@pytest.fixture
def server(tmp_path):
    settings = Settings(db_path=tmp_path / "mcp.db", demo=True)
    Syncer(DemoSource(), Database(settings.db_path)).run()
    return build_server(settings)


def call(server, name, arguments=None):
    result = asyncio.run(server.call_tool(name, arguments or {}))
    return result.content[0].text


def call_list(server, name, arguments=None):
    """List results come back as structured content ({"result": [...]}), one text block per item."""
    result = asyncio.run(server.call_tool(name, arguments or {}))
    return result.structured_content["result"]


def test_tools_are_listed(server):
    names = [tool.name for tool in asyncio.run(server.list_tools())]
    assert names == ["get_coach_context", "get_next_workout", "get_vital_signs", "get_activities", "get_workout"]


def test_coach_context_and_next_workout(server):
    context = call(server, "get_coach_context")
    assert "personal trainer" in context and "Prossimi carichi" in context

    workout = json.loads(call(server, "get_next_workout"))
    assert workout["workout"].startswith("Workout ")
    assert workout["exercises"][0]["suggested_sets"]


def test_vitals_activities_and_workout_detail(server):
    vitals = call_list(server, "get_vital_signs", {"days": 3})
    activities = call_list(server, "get_activities", {"days": 30})

    assert len(vitals) == 3 and vitals[0]["sleep_seconds"]
    manual = next(a for a in activities if a["source"] == "manual")
    detail = json.loads(call(server, "get_workout", {"workout_id": manual["id"]}))
    assert detail["exercises"]
    assert "error" in json.loads(call(server, "get_workout", {"workout_id": 99999}))
