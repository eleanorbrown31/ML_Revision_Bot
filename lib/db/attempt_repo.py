"""Attempt persistence. Every attempt stores a full text snapshot of what was
asked (area/topic/subtopic names, question stem) so a later curriculum
rename never rewrites history (spec §3)."""

from psycopg.rows import dict_row
from psycopg.types.json import Json

from lib.db.client import get_pool


def create_attempt(
    session_id: str,
    question: dict,
    response_text: str | None,
    score: float | None,
    rubric_points_hit: dict | None,
    self_rated_confidence: int | None,
    seconds_taken: int | None,
    hint_used: bool,
    critique: str | None = None,
    marker_prompt_version_id: str | None = None,
    marker_model: str | None = None,
) -> str:
    """`question` must be the joined dict from lib.db.question_repo (it carries
    area_name/topic_name/subtopic_name/topic_id/subtopic_id for the snapshot)."""
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into attempt (
                    session_id, question_id, subtopic_id, topic_id,
                    area_name_snapshot, topic_name_snapshot, subtopic_name_snapshot,
                    difficulty, question_stem_snapshot,
                    response, score, rubric_points_hit, critique,
                    self_rated_confidence, seconds_taken, hint_used,
                    marker_prompt_version_id, marker_model
                ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                returning id
                """,
                (
                    session_id, question["id"], question["subtopic_id"], question["topic_id"],
                    question["area_name"], question["topic_name"], question["subtopic_name"],
                    question["difficulty"], question["stem"],
                    response_text, score, Json(rubric_points_hit) if rubric_points_hit else None, critique,
                    self_rated_confidence, seconds_taken, hint_used,
                    marker_prompt_version_id, marker_model,
                ),
            )
            attempt_id = cur.fetchone()[0]
        conn.commit()
    return attempt_id


def recent_question_ids_bulk(subtopic_ids: list[str], limit: int = 5) -> dict[str, set[str]]:
    """Bulk variant of recent_question_ids -- one round trip for a whole
    session's worth of subtopics instead of one query per subtopic."""
    if not subtopic_ids:
        return {}
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select subtopic_id, question_id from (
                    select subtopic_id, question_id,
                           row_number() over (partition by subtopic_id order by created_at desc) as rn
                    from attempt
                    where subtopic_id = any(%s)
                ) ranked
                where rn <= %s
                """,
                (subtopic_ids, limit),
            )
            result: dict[str, set[str]] = {sid: set() for sid in subtopic_ids}
            for subtopic_id, question_id in cur.fetchall():
                result[subtopic_id].add(question_id)
            return result


def attempts_over_time(days: int = 90) -> list[dict]:
    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                select date(created_at) as day, count(*) as attempts, avg(score)::float8 as avg_score
                from attempt
                where created_at >= now() - (%s * interval '1 day') and score is not null
                group by date(created_at)
                order by day
                """,
                (days,),
            )
            return cur.fetchall()


def subtopic_attempt_counts(subtopic_ids: list[str]) -> dict[str, int]:
    """Used by lib.selection.pick_subtopic_for_topic to find the
    least-attempted subtopic within a topic (coverage gap)."""
    if not subtopic_ids:
        return {}
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select subtopic_id, count(*) from attempt where subtopic_id = any(%s) group by subtopic_id",
                (subtopic_ids,),
            )
            counts = {row[0]: row[1] for row in cur.fetchall()}
    return {sid: counts.get(sid, 0) for sid in subtopic_ids}


def count_attempts_in_session(session_id: str) -> int:
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) from attempt where session_id = %s", (session_id,))
            return cur.fetchone()[0]
