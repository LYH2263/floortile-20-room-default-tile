from fastapi import APIRouter, HTTPException

from app.repositories import rooms as room_repo
from app.repositories import tiles as tile_repo
from app.schemas.room import RoomPreferenceRequest

router = APIRouter(tags=["rooms"])


@router.get("/rooms")
def list_rooms():
    return {"items": room_repo.list_rooms()}


@router.get("/rooms/{room_id}")
def get_room(room_id: int):
    row = room_repo.get_room(room_id)
    if not row:
        raise HTTPException(404, "room not found")
    return row


@router.put("/rooms/{room_id}/preferred-tile")
def set_preferred_tile(room_id: int, body: RoomPreferenceRequest):
    """Set or clear (tile_id=null) a room's preferred tile.

    Only updates the rooms row — never writes to calc_runs; history rows are
    created solely by an estimate with save=true.
    """
    if not room_repo.get_room(room_id):
        raise HTTPException(404, "room not found")
    if body.tile_id is not None:
        tile = tile_repo.get_tile(body.tile_id)
        if not tile:
            raise HTTPException(404, "tile not found")
        if tile.get("data_quality") == "dirty":
            raise HTTPException(422, "tile marked dirty; cannot set as preference")
    room_repo.set_preferred_tile(room_id, body.tile_id)
    return room_repo.get_room(room_id)
