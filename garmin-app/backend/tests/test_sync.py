import threading

import pytest
from helpers import FakeSource, make_raw

from garmin_hub.db import Database
from garmin_hub.sync import SyncInProgress, Syncer


@pytest.fixture
def db(tmp_path):
    return Database(tmp_path / "test.db")


def history(count):
    return [make_raw(i) for i in range(count)]


def test_first_sync_imports_whole_history(db):
    source = FakeSource(history(120))

    result = Syncer(source, db, page_size=50).run()

    assert (result.new, result.updated, result.total) == (120, 0, 120)
    assert result.history_complete
    assert [start for start, _ in source.calls] == [0, 50, 100]


def test_refresh_without_changes_reads_only_the_newest_page(db):
    source = FakeSource(history(120))
    syncer = Syncer(source, db, page_size=50)
    syncer.run()
    source.calls.clear()

    result = syncer.run()

    assert (result.new, result.updated, result.total) == (0, 0, 120)
    assert source.calls == [(0, 50)]


def test_refresh_picks_up_new_and_renamed_activities(db):
    source = FakeSource(history(120))
    syncer = Syncer(source, db, page_size=50)
    syncer.run()
    source.activities.insert(0, make_raw(-1, activity_id=999))
    source.activities[5]["activityName"] = "Rinominata su Garmin"

    result = syncer.run()

    assert (result.new, result.updated, result.total) == (1, 1, 121)
    newest = db.list_activities(limit=6)
    assert newest[0]["id"] == 999
    assert newest[5]["name"] == "Rinominata su Garmin"


def test_capped_syncs_resume_the_backfill_until_history_is_complete(db):
    source = FakeSource(history(230))
    syncer = Syncer(source, db, page_size=50)

    progress = []
    for _ in range(4):
        result = syncer.run(max_pages=2)
        progress.append((result.total, result.history_complete))

    assert progress == [(100, False), (145, False), (190, False), (230, True)]
    source.calls.clear()
    syncer.run(max_pages=2)
    assert source.calls == [(0, 50)]


def test_full_sync_rereads_every_page(db):
    source = FakeSource(history(120))
    syncer = Syncer(source, db, page_size=50)
    syncer.run()
    source.calls.clear()

    result = syncer.run(full=True)

    assert result.new == 0
    assert [start for start, _ in source.calls] == [0, 50, 100]


def test_concurrent_sync_is_rejected(db):
    started, release = threading.Event(), threading.Event()

    class SlowSource(FakeSource):
        def fetch_activities(self, start, limit):
            started.set()
            release.wait(5)
            return super().fetch_activities(start, limit)

    syncer = Syncer(SlowSource(history(3)), db, page_size=50)
    worker = threading.Thread(target=syncer.run)
    worker.start()
    try:
        assert started.wait(5)
        with pytest.raises(SyncInProgress):
            syncer.run()
    finally:
        release.set()
        worker.join(5)
    assert db.count_activities() == 3
