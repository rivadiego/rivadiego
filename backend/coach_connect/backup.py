"""Database and Garmin tokens kept in a private Hugging Face dataset, for hosts whose disk is wiped on restart."""

from __future__ import annotations

import logging
import shutil
import sqlite3
import tempfile
import threading
from contextlib import closing
from pathlib import Path
from typing import Any

from .config import Settings
from .sources import TOKEN_FILE

log = logging.getLogger(__name__)

DB_FILE = "garmin.db"
RETRY_S = 60.0


class CloudBackup:
    def __init__(
        self, repo_id: str, db_path: Path, token_dir: Path, *, api: Any, delay_s: float = 5.0
    ) -> None:
        self.repo_id = repo_id
        self.db_path = db_path
        self.token_dir = token_dir
        self.api = api
        self.delay_s = delay_s
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None

    def restore(self) -> None:
        """Bring back the saved copies after a restart, before the database is opened.

        Errors other than "nothing saved yet" propagate: starting with an empty database would overwrite the
        saved one at the first backup.
        """
        from huggingface_hub.errors import EntryNotFoundError, RepositoryNotFoundError, RevisionNotFoundError

        for name, target in ((DB_FILE, self.db_path), (TOKEN_FILE, self.token_dir / TOKEN_FILE)):
            if target.exists():
                continue
            try:
                downloaded = self.api.hf_hub_download(self.repo_id, name, repo_type="dataset")
            except (EntryNotFoundError, RepositoryNotFoundError, RevisionNotFoundError):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(downloaded, target)
            log.info("Ripristinato %s dal dataset %s", name, self.repo_id)

    def schedule(self) -> None:
        """Save shortly after a change: a burst of changes ends up in one commit."""
        self._start_timer(self.delay_s)

    def flush(self) -> None:
        """Save now if a change is still waiting, e.g. when the server shuts down."""
        with self._lock:
            timer, self._timer = self._timer, None
        if timer is not None:
            timer.cancel()
            self.upload()

    def upload(self) -> None:
        from huggingface_hub import CommitOperationAdd

        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / DB_FILE
            # A consistent copy even while requests keep writing.
            with closing(sqlite3.connect(self.db_path)) as source, closing(sqlite3.connect(snapshot)) as copy:
                source.backup(copy)
            operations = [CommitOperationAdd(path_in_repo=DB_FILE, path_or_fileobj=str(snapshot))]
            tokens = self.token_dir / TOKEN_FILE
            if tokens.exists():
                operations.append(CommitOperationAdd(path_in_repo=TOKEN_FILE, path_or_fileobj=str(tokens)))
            self.api.create_commit(
                self.repo_id, operations, commit_message="Backup Coach Connect", repo_type="dataset"
            )

    def _start_timer(self, delay_s: float) -> None:
        with self._lock:
            if self._timer is None:
                self._timer = threading.Timer(delay_s, self._scheduled_upload)
                self._timer.daemon = True
                self._timer.start()

    def _scheduled_upload(self) -> None:
        with self._lock:
            self._timer = None
        try:
            self.upload()
        except Exception:
            log.exception("Backup sul dataset %s non riuscito: riprovo tra %.0f s", self.repo_id, RETRY_S)
            self._start_timer(RETRY_S)


def cloud_backup(settings: Settings) -> CloudBackup | None:
    if not (settings.hf_token and settings.hf_data_repo):
        return None
    from huggingface_hub import HfApi

    return CloudBackup(
        settings.hf_data_repo, settings.db_path, settings.token_dir, api=HfApi(token=settings.hf_token)
    )
