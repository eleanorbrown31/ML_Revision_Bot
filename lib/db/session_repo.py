"""Quiz session lifecycle."""

from psycopg.types.json import Json

from lib.db.client import get_pool


def start_session(mode: str, config: dict) -> str:
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "insert into session (mode, config) values (%s, %s) returning id",
                (mode, Json(config)),
            )
            session_id = cur.fetchone()[0]
        conn.commit()
    return session_id


def end_session(session_id: str) -> None:
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute("update session set ended_at = now() where id = %s", (session_id,))
        conn.commit()
