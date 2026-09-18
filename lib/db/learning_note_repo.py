"""Persistence for learner-authored reflections and teach-backs."""

from lib.db.client import get_pool
from psycopg.rows import dict_row


def create_learning_note(
    *,
    session_id: str | None,
    topic_id: str | None,
    content: str,
    kind: str = "reflection",
    self_rated_confidence: int | None = None,
    misconception_tag: str | None = None,
) -> str:
    """Store a note exactly as the learner wrote it; it is not LLM-marked."""
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into learning_note
                    (session_id, topic_id, kind, content, self_rated_confidence, misconception_tag)
                values (%s, %s, %s, %s, %s, %s)
                returning id
                """,
                (session_id, topic_id, kind, content, self_rated_confidence, misconception_tag),
            )
            note_id = cur.fetchone()[0]
        conn.commit()
    return note_id


def list_recent(limit: int = 10) -> list[dict]:
    """Return recent reflections with enough context to make them readable."""
    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                select n.content, n.kind, n.self_rated_confidence, n.misconception_tag,
                       n.created_at, t.name as topic_name
                from learning_note n
                left join topic t on t.id = n.topic_id
                order by n.created_at desc
                limit %s
                """,
                (limit,),
            )
            return cur.fetchall()
