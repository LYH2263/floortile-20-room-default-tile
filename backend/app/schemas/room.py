from pydantic import BaseModel


class RoomPreferenceIn(BaseModel):
    tile_id: int
