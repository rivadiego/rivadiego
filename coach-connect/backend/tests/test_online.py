import sqlite3
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from garminconnect import GarminConnectAuthenticationError
from helpers import FakeSource, offline_coach
from huggingface_hub.errors import EntryNotFoundError

from coach_connect import api as api_module
from coach_connect import garmin_auth
from coach_connect.api import create_app
from coach_connect.backup import DB_FILE, CloudBackup
from coach_connect.config import Settings
from coach_connect.sources import TOKEN_FILE, DemoSource, GarminSource

WORKOUT = {
    "plan_workout": "A",
    "exercises": [{"exercise_id": "incline_barbell_bench", "sets": [{"weight_kg": 60, "reps": 6}]}],
}


class FakeHub:
    """The two Hugging Face calls the backup makes, on a dict of files."""

    def __init__(self, tmp_path: Path, files: dict[str, bytes] | None = None) -> None:
        self.tmp_path = tmp_path
        self.files = dict(files or {})
        self.commits: list[dict[str, bytes]] = []

    def hf_hub_download(self, repo_id: str, filename: str, repo_type: str) -> str:
        assert (repo_id, repo_type) == ("me/data", "dataset")
        if filename not in self.files:
            raise EntryNotFoundError(f"{filename} non c'è")
        path = self.tmp_path / "downloads" / filename
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(self.files[filename])
        return str(path)

    def create_commit(self, repo_id: str, operations, commit_message: str, repo_type: str) -> None:
        commit = {op.path_in_repo: Path(op.path_or_fileobj).read_bytes() for op in operations}
        self.commits.append(commit)
        self.files.update(commit)


def backup_for(tmp_path, hub, delay_s=5.0):
    return CloudBackup("me/data", tmp_path / "data" / "garmin.db", tmp_path / "tokens", api=hub, delay_s=delay_s)


def tables(db_bytes: bytes, tmp_path: Path) -> set[str]:
    path = tmp_path / "check.db"
    path.write_bytes(db_bytes)
    with sqlite3.connect(path) as conn:
        return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def test_restore_brings_back_database_and_tokens(tmp_path):
    saved_db = tmp_path / "saved.db"
    with sqlite3.connect(saved_db) as conn:
        conn.execute("CREATE TABLE saved (x)")
    hub = FakeHub(tmp_path, {DB_FILE: saved_db.read_bytes(), TOKEN_FILE: b'{"t": 1}'})
    backup = backup_for(tmp_path, hub)

    backup.restore()

    assert "saved" in tables((tmp_path / "data" / "garmin.db").read_bytes(), tmp_path)
    assert (tmp_path / "tokens" / TOKEN_FILE).read_bytes() == b'{"t": 1}'


def test_restore_keeps_local_files_and_tolerates_an_empty_dataset(tmp_path):
    (tmp_path / "tokens").mkdir()
    (tmp_path / "tokens" / TOKEN_FILE).write_text("locale")
    backup = backup_for(tmp_path, FakeHub(tmp_path, {TOKEN_FILE: b"remoto"}))

    backup.restore()

    assert (tmp_path / "tokens" / TOKEN_FILE).read_text() == "locale"
    assert not (tmp_path / "data" / "garmin.db").exists()


def test_app_refuses_to_start_when_the_saved_data_cannot_be_read(tmp_path, monkeypatch):
    class Unreachable(FakeHub):
        def hf_hub_download(self, *args, **kwargs):
            raise ConnectionError("Hugging Face non risponde")

    backup = backup_for(tmp_path, Unreachable(tmp_path))
    monkeypatch.setattr(api_module, "cloud_backup", lambda settings: backup)

    with pytest.raises(ConnectionError):
        create_app(Settings(db_path=backup.db_path), FakeSource([]), offline_coach(Settings()))


def test_changes_are_saved_in_one_commit_with_a_consistent_copy(tmp_path, monkeypatch):
    hub = FakeHub(tmp_path)
    backup = backup_for(tmp_path, hub, delay_s=1.0)
    monkeypatch.setattr(api_module, "cloud_backup", lambda settings: backup)
    settings = Settings(db_path=backup.db_path, token_dir=backup.token_dir)
    client = TestClient(create_app(settings, FakeSource([]), offline_coach(settings)))

    client.get("/api/feed")
    assert client.post("/api/workouts", json=WORKOUT).status_code == 201
    assert client.post("/api/workouts", json=WORKOUT).status_code == 201
    time.sleep(1.8)

    assert len(hub.commits) == 1
    assert set(hub.commits[0]) == {DB_FILE}
    assert {"workouts", "workout_sets"} <= tables(hub.commits[0][DB_FILE], tmp_path)


def test_backup_on_request_reports_the_outcome(tmp_path, monkeypatch):
    class ReadOnly(FakeHub):
        def create_commit(self, *args, **kwargs):
            raise PermissionError("403 Forbidden: token di sola lettura")

    for hub, expected in ((FakeHub(tmp_path), 200), (ReadOnly(tmp_path), 502)):
        backup = backup_for(tmp_path, hub, delay_s=0.1)
        monkeypatch.setattr(api_module, "cloud_backup", lambda settings, backup=backup: backup)
        settings = Settings(db_path=backup.db_path, token_dir=backup.token_dir)
        client = TestClient(create_app(settings, FakeSource([]), offline_coach(settings)))

        response = client.post("/api/backup")
        time.sleep(0.3)

        assert response.status_code == expected
        if expected == 200:
            assert len(hub.commits) == 1
        else:
            assert response.json() == {"code": "backup_failed", "detail": "403 Forbidden: token di sola lettura"}


def test_without_backup_settings_the_endpoint_says_so(tmp_path):
    settings = Settings(db_path=tmp_path / "api.db")
    client = TestClient(create_app(settings, FakeSource([]), offline_coach(settings)))

    assert client.post("/api/backup").status_code == 404


def test_flush_saves_the_pending_change_with_the_tokens(tmp_path):
    hub = FakeHub(tmp_path)
    backup = backup_for(tmp_path, hub)
    backup.db_path.parent.mkdir()
    sqlite3.connect(backup.db_path).close()
    backup.token_dir.mkdir()
    (backup.token_dir / TOKEN_FILE).write_text("{}")

    backup.schedule()
    backup.flush()

    assert len(hub.commits) == 1
    assert set(hub.commits[0]) == {DB_FILE, TOKEN_FILE}


class FakeGarmin:
    """Garmin login: accounts starting with "mfa" ask for the code 123456."""

    def __init__(self, email: str, password: str, return_on_mfa: bool = False) -> None:
        assert return_on_mfa
        self.email, self.password = email, password
        self.client = SimpleNamespace(dump=lambda path: (Path(path) / TOKEN_FILE).write_text('{"di": "token"}'))

    def login(self, tokenstore=None):
        if self.password != "giusta":
            raise GarminConnectAuthenticationError("401 Unauthorized")
        return ("needs_mfa", None) if self.email.startswith("mfa") else (None, None)

    def resume_login(self, client_state, code):
        if code != "123456":
            raise GarminConnectAuthenticationError("wrong code")
        return (None, None)


@pytest.fixture
def garmin_client(tmp_path, monkeypatch):
    monkeypatch.setattr(garmin_auth, "Garmin", FakeGarmin)
    settings = Settings(db_path=tmp_path / "api.db", token_dir=tmp_path / "tokens")
    return TestClient(create_app(settings, GarminSource(settings.token_dir), offline_coach(settings)))


def test_garmin_login_with_verification_code(garmin_client):
    assert not garmin_client.get("/api/status").json()["garmin_ready"]

    started = garmin_client.post("/api/garmin/login", json={"email": "mfa@example.com", "password": "giusta"})
    assert started.json() == {"status": "needs_code"}

    wrong = garmin_client.post("/api/garmin/code", json={"code": "000000"})
    assert (wrong.status_code, wrong.json()["code"]) == (400, "garmin_login_failed")

    confirmed = garmin_client.post("/api/garmin/code", json={"code": "123456"})
    assert confirmed.json() == {"status": "connected"}
    assert garmin_client.get("/api/status").json()["garmin_ready"]


def test_garmin_login_without_code_and_errors(garmin_client):
    rejected = garmin_client.post("/api/garmin/login", json={"email": "io@example.com", "password": "sbagliata"})
    assert (rejected.status_code, rejected.json()["code"]) == (400, "garmin_login_failed")

    expired = garmin_client.post("/api/garmin/code", json={"code": "123456"})
    assert (expired.status_code, expired.json()["code"]) == (409, "garmin_code_expired")

    connected = garmin_client.post("/api/garmin/login", json={"email": "io@example.com", "password": "giusta"})
    assert connected.json() == {"status": "connected"}
    assert garmin_client.get("/api/status").json()["garmin_ready"]


def test_garmin_login_is_not_needed_with_demo_data(tmp_path):
    settings = Settings(db_path=tmp_path / "api.db", demo=True)
    client = TestClient(create_app(settings, DemoSource(), offline_coach(settings)))

    response = client.post("/api/garmin/login", json={"email": "io@example.com", "password": "giusta"})

    assert response.status_code == 409


def test_backend_serves_the_web_app(tmp_path):
    web = tmp_path / "web"
    (web / "_expo" / "static").mkdir(parents=True)
    (web / "index.html").write_text("<html>Coach Connect</html>")
    (web / "_expo" / "static" / "entry.js").write_text("console.log('app')")
    (tmp_path / "secret.txt").write_text("non servire")
    settings = Settings(db_path=tmp_path / "api.db", web_dir=web, api_token="codice")
    client = TestClient(create_app(settings, FakeSource([]), offline_coach(settings)))

    assert client.get("/").text == "<html>Coach Connect</html>"
    assert client.get("/scheda").text == "<html>Coach Connect</html>"
    assert client.get("/_expo/static/entry.js").text == "console.log('app')"
    assert "non servire" not in client.get("/%2e%2e/secret.txt").text
    assert client.get("/api/nope", headers={"Authorization": "Bearer codice"}).status_code == 404
    assert client.get("/api/feed").status_code == 401
    assert client.get("/docs").status_code == 200


def test_online_the_access_code_is_mandatory(tmp_path, monkeypatch):
    monkeypatch.setenv("SPACE_ID", "me/coach-connect")
    settings = Settings(db_path=tmp_path / "api.db")

    with pytest.raises(RuntimeError, match="API_TOKEN"):
        create_app(settings, FakeSource([]), offline_coach(settings))
