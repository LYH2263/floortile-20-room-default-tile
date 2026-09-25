from fastapi import APIRouter, HTTPException

from app.repositories import rooms as room_repo
from app.repositories import tiles as tile_repo
from app.schemas.room import RoomPreferenceIn

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
def set_preferred_tile(room_id: int, body: RoomPreferenceIn):
    # Preference edits only touch the rooms table; they must never
    # create calc_runs entries (history comes from explicit estimates).
    if not room_repo.get_room(room_id):
        raise HTTPException(404, "room not found")
    if not tile_repo.get_tile(body.tile_id):
        raise HTTPException(404, "tile not found")
    room_repo.set_preferred_tile(room_id, body.tile_id)
    return room_repo.get_room(room_id)


@router.delete("/rooms/{room_id}/preferred-tile")
def clear_preferred_tile(room_id: int):
    if not room_repo.get_room(room_id):
        raise HTTPException(404, "room not found")
    room_repo.clear_preferred_tile(room_id)
    return room_repo.get_room(room_id)
