import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="floortile-test-")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _runs_count(client):
    return len(client.get("/api/runs").json()["items"])


def test_set_and_clear_preference(client):
    # set: room 1 -> tile 2 (800x800)
    r = client.put("/api/rooms/1/preferred-tile", json={"tile_id": 2})
    assert r.status_code == 200
    assert r.json()["preferred_tile_id"] == 2
    assert r.json()["preferred_tile_name"] == "800x800"

    # detail and list read from the same field
    detail = client.get("/api/rooms/1").json()
    listed = {row["id"]: row for row in client.get("/api/rooms").json()["items"]}[1]
    assert detail["preferred_tile_id"] == 2
    assert listed["preferred_tile_id"] == 2
    assert listed["preferred_tile_name"] == detail["preferred_tile_name"] == "800x800"

    # clear: back to no preference (system default applies in the bench)
    r = client.put("/api/rooms/1/preferred-tile", json={"tile_id": None})
    assert r.status_code == 200
    assert r.json()["preferred_tile_id"] is None
    assert client.get("/api/rooms/1").json()["preferred_tile_id"] is None
    assert {row["id"]: row for row in client.get("/api/rooms").json()["items"]}[1][
        "preferred_tile_id"
    ] is None


def test_preference_validation(client):
    assert client.put("/api/rooms/1/preferred-tile", json={"tile_id": 999}).status_code == 404
    # tile 3 is the seeded dirty tile (zero area)
    assert client.put("/api/rooms/1/preferred-tile", json={"tile_id": 3}).status_code == 422
    assert client.put("/api/rooms/999/preferred-tile", json={"tile_id": 1}).status_code == 404


def test_preference_changes_write_no_history(client):
    before = _runs_count(client)
    assert client.put("/api/rooms/2/preferred-tile", json={"tile_id": 2}).status_code == 200
    assert client.put("/api/rooms/2/preferred-tile", json={"tile_id": None}).status_code == 200
    assert _runs_count(client) == before


def test_runs_only_created_when_save_checked(client):
    before = _runs_count(client)
    # preview (save=false) must not persist
    r = client.get("/api/estimate", params={"room_id": 1, "tile_id": 1})
    assert r.status_code == 200
    assert r.json()["run_id"] is None
    assert _runs_count(client) == before

    # explicit save=true persists exactly one run
    r = client.post(
        "/api/estimate", json={"room_id": 1, "tile_id": 1, "save": True, "note": "t"}
    )
    assert r.status_code == 200
    assert r.json()["run_id"] is not None
    assert _runs_count(client) == before + 1


def test_default_tile_setting_seeded(client):
    settings = client.get("/api/settings").json()
    tiles = client.get("/api/tiles").json()["items"]
    seeded_600 = next(t for t in tiles if t["name"] == "600x600")
    assert settings["default_tile_id"] == str(seeded_600["id"])
