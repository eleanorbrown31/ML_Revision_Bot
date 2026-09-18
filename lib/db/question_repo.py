"""Question bank CRUD.

Questions are never deleted -- status moves draft -> active -> retired only,
per spec §7 rule 3 (soft-delete via status/is_active, no hard delete in the UI).
"""

from psycopg.rows import dict_row
from psycopg.types.json import Json

from lib.db.client import get_pool

VALID_STATUSES = ("draft", "active", "retired")

_LIST_SELECT = """
    select
        q.id, q.subtopic_id, q.difficulty, q.format, q.stem, q.payload,
        q.answer_key, q.explanation, q.distractor_notes, q.status, q.source,
        q.generator_model, q.created_at,
        st.name as subtopic_name, t.id as topic_id, t.name as topic_name,
        a.id as area_id, a.name as area_name
    from question q
    join subtopic st on st.id = q.subtopic_id
    join topic t on t.id = st.topic_id
    join area a on a.id = t.area_id
"""


def list_questions(
    subtopic_id: str | None = None,
    topic_id: str | None = None,
    status: str | None = None,
    difficulty: str | None = None,
    format: str | None = None,
) -> list[dict]:
    clauses = []
    params: list = []
    if subtopic_id:
        clauses.append("q.subtopic_id = %s")
        params.append(subtopic_id)
    if topic_id:
        clauses.append("t.id = %s")
        params.append(topic_id)
    if status:
        clauses.append("q.status = %s")
        params.append(status)
    if difficulty:
        clauses.append("q.difficulty = %s")
        params.append(difficulty)
    if format:
        clauses.append("q.format = %s")
        params.append(format)

    query = _LIST_SELECT
    if clauses:
        query += " where " + " and ".join(clauses)
    query += " order by q.created_at desc"

    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_question(question_id: str) -> dict | None:
    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(_LIST_SELECT + " where q.id = %s", (question_id,))
            return cur.fetchone()


def list_active_questions_for_topics(topic_ids: list[str]) -> list[dict]:
    """Bulk variant of list_active_questions_for_subtopic -- one round trip
    for every topic in a session instead of one query per topic, which is
    what made building a session slow (session_length separate queries)."""
    if not topic_ids:
        return []
    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                _LIST_SELECT + " where q.status = 'active' and t.id = any(%s)",
                (topic_ids,),
            )
            return cur.fetchall()


def topics_with_active_questions() -> set[str]:
    """Topic ids that have at least one active question in any of their
    subtopics -- used by quiz_service to only schedule servable topics."""
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select distinct t.id
                from question q
                join subtopic st on st.id = q.subtopic_id
                join topic t on t.id = st.topic_id
                where q.status = 'active'
                """
            )
            return {row[0] for row in cur.fetchall()}


def create_question(
    subtopic_id: str,
    difficulty: str,
    format: str,
    stem: str,
    payload: dict,
    answer_key: dict,
    explanation: str,
    distractor_notes: dict | None = None,
    status: str = "draft",
    source: str = "authored",
    generator_prompt_version_id: str | None = None,
    generator_model: str | None = None,
) -> str:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")

    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into question (
                    subtopic_id, difficulty, format, stem, payload, answer_key,
                    explanation, distractor_notes, status, source,
                    generator_prompt_version_id, generator_model
                ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                returning id
                """,
                (
                    subtopic_id, difficulty, format, stem, Json(payload), Json(answer_key),
                    explanation, Json(distractor_notes) if distractor_notes else None,
                    status, source, generator_prompt_version_id, generator_model,
                ),
            )
            question_id = cur.fetchone()[0]
        conn.commit()
    return question_id


def update_question(question_id: str, **fields) -> None:
    """Update arbitrary editable columns (stem, payload, answer_key, explanation,
    distractor_notes, difficulty, format). Does not touch status -- use set_status."""
    if not fields:
        return
    json_columns = {"payload", "answer_key", "distractor_notes"}
    set_clauses = []
    params: list = []
    for column, value in fields.items():
        set_clauses.append(f"{column} = %s")
        params.append(Json(value) if column in json_columns and value is not None else value)
    params.append(question_id)

    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"update question set {', '.join(set_clauses)} where id = %s",
                params,
            )
        conn.commit()


def set_status(question_id: str, status: str) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute("update question set status = %s where id = %s", (status, question_id))
        conn.commit()
