"""Read helpers over the area/topic/subtopic tree (active nodes only)."""

from psycopg.rows import dict_row

from lib.db.client import get_pool


def list_areas() -> list[dict]:
    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "select id, name, sort_order from area where is_active = true order by sort_order, name"
            )
            return cur.fetchall()


def list_topics(area_id: str | None = None) -> list[dict]:
    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if area_id:
                cur.execute(
                    "select id, area_id, name, description, exam_weight "
                    "from topic where is_active = true and area_id = %s order by name",
                    (area_id,),
                )
            else:
                cur.execute(
                    "select id, area_id, name, description, exam_weight "
                    "from topic where is_active = true order by name"
                )
            return cur.fetchall()


def list_subtopics(topic_id: str | None = None) -> list[dict]:
    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if topic_id:
                cur.execute(
                    "select id, topic_id, name, learning_objectives "
                    "from subtopic where is_active = true and topic_id = %s order by name",
                    (topic_id,),
                )
            else:
                cur.execute(
                    "select id, topic_id, name, learning_objectives "
                    "from subtopic where is_active = true order by name"
                )
            return cur.fetchall()


def list_subtopics_for_topics(topic_ids: list[str]) -> list[dict]:
    """Bulk variant of list_subtopics -- one round trip for a whole set of
    topics instead of one query per topic."""
    if not topic_ids:
        return []
    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "select id, topic_id, name, learning_objectives "
                "from subtopic where is_active = true and topic_id = any(%s) order by name",
                (topic_ids,),
            )
            return cur.fetchall()


def get_topic(topic_id: str) -> dict | None:
    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("select * from topic where id = %s", (topic_id,))
            return cur.fetchone()


def get_subtopic(subtopic_id: str) -> dict | None:
    with get_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("select * from subtopic where id = %s", (subtopic_id,))
            return cur.fetchone()


def get_curriculum_tree() -> list[dict]:
    """Areas, each with nested topics, each with nested subtopics -- for cascading pickers."""
    areas = list_areas()
    topics = list_topics()
    subtopics = list_subtopics()

    topics_by_area: dict[str, list[dict]] = {}
    for t in topics:
        topics_by_area.setdefault(t["area_id"], []).append(t)

    subtopics_by_topic: dict[str, list[dict]] = {}
    for s in subtopics:
        subtopics_by_topic.setdefault(s["topic_id"], []).append(s)

    tree = []
    for area in areas:
        area_topics = []
        for topic in topics_by_area.get(area["id"], []):
            area_topics.append({**topic, "subtopics": subtopics_by_topic.get(topic["id"], [])})
        tree.append({**area, "topics": area_topics})
    return tree
