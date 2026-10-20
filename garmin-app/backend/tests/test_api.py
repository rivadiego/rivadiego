from fastapi.testclient import TestClient
from helpers import FakeSource, make_raw

from garmin_hub.api import create_app
from garmin_hub.config import Settings
from garmin_hub.sources import DemoSource, GarminRateLimited, GarminSource


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
    assert "python -m garmin_hub login" in response.json()["detail"]
    assert client.get("/api/status").json()["garmin_ready"] is False


def test_garmin_rate_limit_is_reported(tmp_path):
    class Throttled(FakeSource):
        def fetch_activities(self, start, limit):
            raise GarminRateLimited("Garmin sta limitando le richieste")

    response = client_for(tmp_path, Throttled([])).post("/api/sync")

    assert response.status_code == 429
    assert response.json()["code"] == "garmin_rate_limited"
