"""Topic-level mastery reads and the post-attempt upsert."""

from psycopg.rows import dict_row

from lib.db.client import get_pool


def get_mastery(topic_id: str) -> dict | None:
    # Cast numeric columns to float8 -- psycopg maps Postgres `numeric` to
    # decimal.Decimal, which raises TypeError when mixed with the plain
    # floats lib/mastery.py's pure functions do arithmetic with.
    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                select
                    topic_id, ability::float8 as ability, current_band,
                    attempts_count, consecutive_strong, consecutive_weak,
                    last_seen_at, next_due_at,
                    interval_days::float8 as interval_days, ease::float8 as ease
                from mastery where topic_id = %s
                """,
                (topic_id,),
            )
            return cur.fetchone()


def list_topics_for_scheduling() -> list[dict]:
    """Active topics joined with their mastery row and area, shaped for
    lib/selection.py's compute_priority()/select_session_topics()."""
    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                select
                    t.id, t.area_id, t.name as topic_name, t.exam_weight::float8 as exam_weight,
                    a.name as area_name,
                    coalesce(m.ability, 0)::float8 as ability,
                    coalesce(m.attempts_count, 0) as attempts_count,
                    m.next_due_at, m.last_seen_at, m.current_band
                from topic t
                join area a on a.id = t.area_id
                left join mastery m on m.topic_id = t.id
                where t.is_active = true
                order by t.name
                """
            )
            return cur.fetchall()


def upsert_after_attempt(topic_id: str, updated: dict, seen_at) -> None:
    """updated: {ability, current_band, attempts_count, consecutive_strong,
    consecutive_weak, ease, interval_days} from lib.mastery.update_mastery_after_attempt().
    next_due_at is derived here from interval_days since that requires "now"."""
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                update mastery set
                    ability = %s,
                    current_band = %s,
                    attempts_count = %s,
                    consecutive_strong = %s,
                    consecutive_weak = %s,
                    ease = %s,
                    interval_days = %s,
                    last_seen_at = %s,
                    next_due_at = %s + (%s * interval '1 day')
                where topic_id = %s
                """,
                (
                    updated["ability"],
                    updated["current_band"],
                    updated["attempts_count"],
                    updated["consecutive_strong"],
                    updated["consecutive_weak"],
                    updated["ease"],
                    updated["interval_days"],
                    seen_at,
                    seen_at,
                    updated["interval_days"],
                    topic_id,
                ),
            )
        conn.commit()


def rollup_by_area() -> list[dict]:
    """Mean ability per area, weighted equally across topics -- for the dashboard."""
    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                select a.id, a.name, avg(coalesce(m.ability, 0))::float8 as avg_ability, count(t.id) as topic_count
                from area a
                join topic t on t.area_id = a.id and t.is_active = true
                left join mastery m on m.topic_id = t.id
                where a.is_active = true
                group by a.id, a.name
                order by a.sort_order, a.name
                """
            )
            return cur.fetchall()


def weakest_topics(limit: int = 10) -> list[dict]:
    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                select t.id, t.name as topic_name, a.name as area_name,
                       coalesce(m.ability, 0)::float8 as ability, coalesce(m.current_band, 'F1') as current_band,
                       coalesce(m.attempts_count, 0) as attempts_count
                from topic t
                join area a on a.id = t.area_id
                left join mastery m on m.topic_id = t.id
                where t.is_active = true
                order by ability asc, t.name
                limit %s
                """,
                (limit,),
            )
            return cur.fetchall()


def due_today_count() -> int:
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select count(*) from mastery where next_due_at is not null and next_due_at <= now()"
            )
            return cur.fetchone()[0]
