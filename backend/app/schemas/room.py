from pydantic import BaseModel


class RoomPreferenceRequest(BaseModel):
    tile_id: int | None = None
