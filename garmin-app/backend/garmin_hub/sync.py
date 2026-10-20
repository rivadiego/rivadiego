"""Pull activities from a source into the local database."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from .db import Database
from .normalize import normalize_activity
from .sources import ActivitySource

HISTORY_COMPLETE = "history_complete"
LAST_SYNC_AT = "last_sync_at"
# The backfill resumes this many activities before the stored count, so that a few activities
# deleted on Garmin (which shift the list offsets) don't make it skip older ones.
BACKFILL_OVERLAP = 5


class SyncInProgress(Exception):
    """Raised when a sync is requested while another one is still running."""


@dataclass(frozen=True)
class SyncResult:
    mode: str
    new: int
    updated: int
    pages: int
    total: int
    last_sync_at: str
    history_complete: bool


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class Syncer:
    def __init__(
        self,
        source: ActivitySource,
        db: Database,
        *,
        page_size: int = 50,
        pause_s: float = 0.0,
    ) -> None:
        self.source = source
        self.db = db
        self.page_size = page_size
        self.pause_s = pause_s
        self._lock = threading.Lock()
        self._new = 0
        self._updated = 0

    def run(
        self,
        *,
        full: bool = False,
        max_pages: int | None = None,
        progress: Callable[[int, int], None] | None = None,
    ) -> SyncResult:
        """Sync newest-first pages of activities.

        A normal sync stops at the first page that brings nothing new. Until the whole history has
        been imported once, it also resumes the backfill of older activities where the previous
        sync stopped; `max_pages` caps the Garmin requests made by a single run. `full` re-reads
        every page.
        """
        if not self._lock.acquire(blocking=False):
            raise SyncInProgress("Sincronizzazione già in corso")
        try:
            self._new = self._updated = 0
            self.source.begin_sync()
            pages, reached_end = self._walk(0, stop_when_known=not full, budget=max_pages, progress=progress)
            if not reached_end and not full and self.db.get_meta(HISTORY_COMPLETE) != "1":
                budget = None if max_pages is None else max_pages - pages
                if budget is None or budget > 0:
                    start = max(0, self.db.count_activities() - BACKFILL_OVERLAP)
                    more, reached_end = self._walk(start, stop_when_known=False, budget=budget, progress=progress)
                    pages += more
            if reached_end:
                self.db.set_meta(HISTORY_COMPLETE, "1")
            last_sync_at = utc_now_iso()
            self.db.set_meta(LAST_SYNC_AT, last_sync_at)
            return SyncResult(
                mode=self.source.mode,
                new=self._new,
                updated=self._updated,
                pages=pages,
                total=self.db.count_activities(),
                last_sync_at=last_sync_at,
                history_complete=self.db.get_meta(HISTORY_COMPLETE) == "1",
            )
        finally:
            self._lock.release()

    def _walk(
        self,
        offset: int,
        *,
        stop_when_known: bool,
        budget: int | None,
        progress: Callable[[int, int], None] | None,
    ) -> tuple[int, bool]:
        """Read pages from `offset`. Returns (pages read, whether the end of the history was reached)."""
        pages = 0
        while budget is None or pages < budget:
            if pages and self.pause_s:
                time.sleep(self.pause_s)
            batch = self.source.fetch_activities(offset, self.page_size)
            pages += 1
            if not batch:
                return pages, True
            synced_at = utc_now_iso()
            rows = [{**normalize_activity(raw), "synced_at": synced_at} for raw in batch]
            new, updated = self.db.upsert_activities(rows)
            self._new += new
            self._updated += updated
            if progress:
                progress(offset + len(batch), self._new)
            if len(batch) < self.page_size:
                return pages, True
            if stop_when_known and new == 0:
                return pages, False
            offset += len(batch)
        return pages, False
