"""Editable app config -- currently just exam_date (build plan decision #4:
no fixed exam date yet, so this is a runtime-editable value, not a constant)."""

from datetime import date

from psycopg.types.json import Json

from lib.db.client import get_pool


def get_exam_date() -> date | None:
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select value from config where key = 'exam_date'")
            row = cur.fetchone()
            if not row or row[0] is None:
                return None
            return date.fromisoformat(row[0])


def set_exam_date(value: date | None) -> None:
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "update config set value = %s, updated_at = now() where key = 'exam_date'",
                (Json(value.isoformat() if value else None),),
            )
        conn.commit()


def days_to_exam() -> float | None:
    exam_date = get_exam_date()
    if exam_date is None:
        return None
    return (exam_date - date.today()).days
