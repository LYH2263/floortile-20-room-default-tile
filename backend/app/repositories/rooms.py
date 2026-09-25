from app.db import connect

_SELECT = """
    SELECT r.*, t.name AS preferred_tile_name
    FROM rooms r
    LEFT JOIN tiles t ON t.id = r.preferred_tile_id
"""


def list_rooms():
    conn = connect()
    try:
        return [dict(r) for r in conn.execute(f"{_SELECT} ORDER BY r.id").fetchall()]
    finally:
        conn.close()


def get_room(room_id: int):
    conn = connect()
    try:
        row = conn.execute(f"{_SELECT} WHERE r.id=?", (room_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def set_preferred_tile(room_id: int, tile_id) -> bool:
    """Set or clear (tile_id=None) the room's preferred tile. Returns False if no such room."""
    conn = connect()
    try:
        cur = conn.execute(
            "UPDATE rooms SET preferred_tile_id=? WHERE id=?", (tile_id, room_id)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
