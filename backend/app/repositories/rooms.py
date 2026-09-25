from app.db import connect

# Single source for both list and detail: every room row carries its
# preferred tile id plus the resolved tile name (NULL when no preference).
_BASE_SELECT = """
    SELECT r.*, t.name AS preferred_tile_name
    FROM rooms r
    LEFT JOIN tiles t ON t.id = r.preferred_tile_id
"""


def list_rooms():
    conn = connect()
    try:
        return [dict(r) for r in conn.execute(_BASE_SELECT + " ORDER BY r.id").fetchall()]
    finally:
        conn.close()


def get_room(room_id: int):
    conn = connect()
    try:
        row = conn.execute(_BASE_SELECT + " WHERE r.id=?", (room_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def set_preferred_tile(room_id: int, tile_id: int):
    conn = connect()
    try:
        conn.execute(
            "UPDATE rooms SET preferred_tile_id=? WHERE id=?",
            (tile_id, room_id),
        )
        conn.commit()
    finally:
        conn.close()


def clear_preferred_tile(room_id: int):
    conn = connect()
    try:
        conn.execute(
            "UPDATE rooms SET preferred_tile_id=NULL WHERE id=?",
            (room_id,),
        )
        conn.commit()
    finally:
        conn.close()
