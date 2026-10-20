from fastapi.testclient import TestClient
from helpers import FakeSource, make_raw

from coach_connect.api import create_app
from coach_connect.config import Settings
from coach_connect.sources import DemoSource, GarminRateLimited, GarminSource


def client_for(tmp_path, source, **settings):
    return TestClient(create_app(Settings(db_path=tmp_path / "api.db", **settings), source))


def test_demo_sync_then_list_activities(tmp_path):
    client = client_for(tmp_path, DemoSource(), demo=True)

    status = client.get("/api/status").json()
    assert (status["mode"], status["activity_count"], status["last_sync_at"]) == ("demo", 0, None)

    synced = client.post("/api/sync").json()
    assert synced["new"] > 50
    assert synced["history_complete"]

    page = client.get("/api/activities", params={"limit": 10}).json()
    assert page["total"] == synced["total"]
    assert page["last_sync_at"] == synced["last_sync_at"]
    starts = [a["start_time_utc"] for a in page["items"]]
    assert starts == sorted(starts, reverse=True)
    first = page["items"][0]
    assert first["start_time_utc"].endswith("Z")
    assert "T" in first["start_time_local"]
    assert {"id", "name", "sport", "distance_m", "duration_s", "avg_hr"} <= set(first)


def test_every_demo_refresh_records_a_new_activity(tmp_path):
    client = client_for(tmp_path, DemoSource(), demo=True)
    client.post("/api/sync")

    again = client.post("/api/sync").json()

    assert again["new"] == 1


def test_pagination_and_sport_filter(tmp_path):
    source = FakeSource([make_raw(i, type_key="road_biking" if i % 3 == 0 else "running") for i in range(30)])
    client = client_for(tmp_path, source)
    client.post("/api/sync")

    page = client.get("/api/activities", params={"limit": 10, "offset": 10}).json()
    assert (len(page["items"]), page["total"]) == (10, 30)
    assert page["items"][0]["name"] == "Attività 10"

    bikes = client.get("/api/activities", params={"sport": "bike", "limit": 100}).json()
    assert bikes["total"] == 10
    assert {a["sport"] for a in bikes["items"]} == {"bike"}


def test_api_token_is_enforced(tmp_path):
    client = client_for(tmp_path, FakeSource([]), api_token="segreto")

    assert client.get("/api/activities").status_code == 401
    assert client.post("/api/sync", headers={"Authorization": "Bearer sbagliato"}).status_code == 401
    assert client.get("/api/activities", headers={"Authorization": "Bearer segreto"}).status_code == 200


def test_sync_without_garmin_login_explains_what_to_do(tmp_path):
    client = client_for(tmp_path, GarminSource(tmp_path / "no-tokens"))

    response = client.post("/api/sync")

    assert response.status_code == 503
    assert response.json()["code"] == "garmin_not_authenticated"
    assert "python -m coach_connect login" in response.json()["detail"]
    assert client.get("/api/status").json()["garmin_ready"] is False


def test_log_a_workout_and_see_it_in_the_feed(tmp_path):
    client = client_for(tmp_path, FakeSource([make_raw(0)]))
    client.post("/api/sync")
    body = {
        "plan_workout": "B",
        "started_at": "2026-10-20T07:10:00+02:00",
        "duration_min": 55,
        "exercises": [
            {"exercise_id": "weighted_chin_up", "sets": [{"weight_kg": 10, "reps": 5}, {"weight_kg": 2, "reps": 6}]},
            {"exercise_id": "plank", "sets": [{"seconds": 50}]},
        ],
    }

    created = client.post("/api/workouts", json=body)
    assert created.status_code == 201
    workout = created.json()
    assert workout["name"] == "Workout B · Pull"
    assert workout["start_time_local"] == "2026-10-20T07:10:00"
    assert workout["start_time_utc"] == "2026-10-20T05:10:00Z"

    feed = client.get("/api/feed").json()
    # The workout (05:10 UTC) starts ten minutes after the Garmin run (05:00 UTC).
    assert [(i["key"], i["name"]) for i in feed["items"]] == [
        (f"manual:{workout['id']}", "Workout B · Pull"),
        ("garmin:1000000", "Attività 0"),
    ]
    assert client.get(f"/api/workouts/{workout['id']}").json()["set_count"] == 3

    assert client.delete(f"/api/workouts/{workout['id']}").status_code == 204
    assert client.get(f"/api/workouts/{workout['id']}").status_code == 404


def test_workout_validation(tmp_path):
    client = client_for(tmp_path, FakeSource([]))

    unknown = client.post("/api/workouts", json={"exercises": [{"exercise_id": "nope", "sets": [{"reps": 5}]}]})
    empty = client.post("/api/workouts", json={"exercises": []})
    negative = client.post(
        "/api/workouts", json={"exercises": [{"exercise_id": "plank", "sets": [{"seconds": -5}]}]}
    )

    assert unknown.status_code == 422 and "nope" in unknown.json()["detail"]
    assert empty.status_code == 422
    assert negative.status_code == 422


def test_plan_exercises_and_wellness_endpoints(tmp_path):
    client = client_for(tmp_path, DemoSource(), demo=True)
    synced = client.post("/api/sync").json()
    assert synced["wellness_days"] == 6

    plan = client.get("/api/plan").json()
    assert set(plan["workouts"]) == {"A", "B"}
    assert len(plan["days"]) == 7 and sum(d["is_today"] for d in plan["days"]) == 1
    assert plan["workouts"]["A"]["exercises"][0]["suggestion"]["sets"]

    catalog = client.get("/api/exercises").json()
    assert "Petto" in catalog["groups"]
    assert any(e["id"] == "incline_barbell_bench" for e in catalog["exercises"])

    days = client.get("/api/wellness", params={"days": 3}).json()["days"]
    assert days and days[0]["sleep_seconds"]

    feed = client.get("/api/feed", params={"limit": 200}).json()["items"]
    assert any(i["source"] == "manual" and i["garmin_linked"] for i in feed)


def test_garmin_rate_limit_is_reported(tmp_path):
    class Throttled(FakeSource):
        def fetch_activities(self, start, limit):
            raise GarminRateLimited("Garmin sta limitando le richieste")

    response = client_for(tmp_path, Throttled([])).post("/api/sync")

    assert response.status_code == 429
    assert response.json()["code"] == "garmin_rate_limited"
