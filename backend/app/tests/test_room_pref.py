import os
import sqlite3
import tempfile

# Isolate the test database before any app module reads DATA_DIR.
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="floortile-test-")

from app import seed  # noqa: E402
from app.repositories import history as history_repo  # noqa: E402
from app.repositories import rooms as room_repo  # noqa: E402

seed.init_db()


def test_rooms_start_without_preference():
    for r in room_repo.list_rooms():
        assert r["preferred_tile_id"] is None
        assert r["preferred_tile_name"] is None


def test_set_and_clear_preference():
    room_repo.set_preferred_tile(1, 2)
    try:
        room = room_repo.get_room(1)
        assert room["preferred_tile_id"] == 2
        assert room["preferred_tile_name"] == "800x800"
    finally:
        room_repo.clear_preferred_tile(1)
    room = room_repo.get_room(1)
    assert room["preferred_tile_id"] is None
    assert room["preferred_tile_name"] is None


def test_list_and_detail_share_preference_fields():
    room_repo.set_preferred_tile(1, 2)
    try:
        detail = room_repo.get_room(1)
        listed = next(r for r in room_repo.list_rooms() if r["id"] == 1)
        assert listed["preferred_tile_id"] == detail["preferred_tile_id"] == 2
        assert listed["preferred_tile_name"] == detail["preferred_tile_name"] == "800x800"
    finally:
        room_repo.clear_preferred_tile(1)


def test_preference_ops_do_not_write_history():
    before = len(history_repo.list_runs(limit=1000))
    room_repo.set_preferred_tile(1, 2)
    room_repo.clear_preferred_tile(1)
    assert len(history_repo.list_runs(limit=1000)) == before


def test_init_db_migrates_legacy_rooms_table(tmp_path, monkeypatch):
    db_file = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_file)
    conn.execute(
        """
        CREATE TABLE rooms(
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            length REAL NOT NULL,
            width REAL NOT NULL,
            data_quality TEXT NOT NULL DEFAULT 'clean',
            note TEXT DEFAULT ''
        )
        """
    )
    conn.execute(
        "INSERT INTO rooms(name,length,width,data_quality,note) VALUES ('老房间',4.0,3.0,'clean','')"
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr("app.db.DB_PATH", str(db_file))
    seed.init_db()

    row = room_repo.get_room(1)
    assert row["name"] == "老房间"
    assert row["preferred_tile_id"] is None
    assert row["preferred_tile_name"] is None
