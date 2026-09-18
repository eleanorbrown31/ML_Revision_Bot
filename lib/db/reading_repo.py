"""Learn First readings -- one cached revision reading per topic."""

from psycopg.rows import dict_row

from lib.db.client import get_pool


def get_reading(topic_id: str) -> dict | None:
    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("select * from reading where topic_id = %s", (topic_id,))
            return cur.fetchone()


def topics_with_readings() -> set[str]:
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select topic_id from reading")
            return {row[0] for row in cur.fetchall()}
