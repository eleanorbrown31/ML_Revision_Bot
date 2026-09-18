"""Load hand-written question content from YAML files into the question bank.

Run manually: python scripts/load_questions.py

Content lives as YAML under content/questions/ (searched recursively) rather
than being typed into the Streamlit authoring form -- easier to write, review
and diff in an editor. A file sets a default ``area`` at the top; any question
may override it with its own ``area`` key, so a file generated from one source
note (content/questions/vault/) can span several curriculum areas. This script is the loader half of that pipeline; it
resolves area/topic/subtopic names to ids and upserts questions as
status='active', source='llm'. Matched by (subtopic_id, stem): a question
with a stem already in the DB gets its payload/answer_key/explanation/etc
updated in place (the YAML is the source of truth), anything with a new stem
is inserted fresh. If you're rewriting a question into something different
enough that the stem changes, retire the old row yourself (status='retired')
-- this loader only ever adds or updates, never retires or deletes, per the
project's soft-delete rule.

Runs outside the Streamlit runtime (like apply_migrations.py and
seed_curriculum.py), so it reads the DB URI straight from secrets.toml
rather than going through lib/db/client.py.
"""

import pathlib
import sys
import tomllib

import psycopg
import yaml
from psycopg.types.json import Json

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUESTIONS_DIR = ROOT / "content" / "questions"
SECRETS_PATH = ROOT / ".streamlit" / "secrets.toml"
GENERATOR_MODEL = "claude-sonnet-5"


def load_db_uri() -> str:
    if not SECRETS_PATH.exists():
        sys.exit(f"Missing {SECRETS_PATH}. Copy .streamlit/secrets.toml.example and fill it in first.")
    with open(SECRETS_PATH, "rb") as f:
        secrets = tomllib.load(f)
    try:
        return secrets["supabase"]["db_uri"]
    except KeyError:
        sys.exit("secrets.toml is missing [supabase] db_uri.")


def get_area_id(cur, name: str) -> str:
    cur.execute("select id from area where name = %s and is_active = true", (name,))
    row = cur.fetchone()
    if not row:
        sys.exit(f"Unknown area: {name!r}. Run scripts/seed_curriculum.py first, or check spelling.")
    return row[0]


def get_topic_id(cur, area_id: str, name: str) -> str:
    cur.execute(
        "select id from topic where area_id = %s and name = %s and is_active = true",
        (area_id, name),
    )
    row = cur.fetchone()
    if not row:
        sys.exit(f"Unknown topic: {name!r}.")
    return row[0]


def get_subtopic_id(cur, topic_id: str, name: str) -> str:
    cur.execute(
        "select id from subtopic where topic_id = %s and name = %s and is_active = true",
        (topic_id, name),
    )
    row = cur.fetchone()
    if not row:
        sys.exit(f"Unknown subtopic: {name!r}.")
    return row[0]


def get_existing_question_id(cur, subtopic_id: str, stem: str) -> str | None:
    cur.execute("select id from question where subtopic_id = %s and stem = %s", (subtopic_id, stem))
    row = cur.fetchone()
    return row[0] if row else None


def main() -> None:
    db_uri = load_db_uri()
    files = sorted(QUESTIONS_DIR.rglob("*.yaml"))
    if not files:
        print(f"No question files found under {QUESTIONS_DIR}.")
        return

    inserted = updated = 0
    # prepare_threshold=None: the Supabase transaction pooler doesn't support
    # server-side prepared statements persisting across pooled connections.
    with psycopg.connect(db_uri, autocommit=False, prepare_threshold=None) as conn:
        with conn.cursor() as cur:
            for path in files:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                default_area = data.get("area")
                area_cache: dict[str, str] = {}
                topic_cache: dict[tuple[str, str], str] = {}
                subtopic_cache: dict[tuple[str, str], str] = {}
                file_inserted = file_updated = 0

                for q in data["questions"]:
                    area_name = q.get("area", default_area)
                    if not area_name:
                        sys.exit(f"{path.name}: question {q.get('stem')!r} has no area and the file sets no default.")
                    if area_name not in area_cache:
                        area_cache[area_name] = get_area_id(cur, area_name)
                    area_id = area_cache[area_name]

                    topic_name = q["topic"]
                    topic_key = (area_id, topic_name)
                    if topic_key not in topic_cache:
                        topic_cache[topic_key] = get_topic_id(cur, area_id, topic_name)
                    topic_id = topic_cache[topic_key]

                    subtopic_key = (topic_id, q["subtopic"])
                    if subtopic_key not in subtopic_cache:
                        subtopic_cache[subtopic_key] = get_subtopic_id(cur, topic_id, q["subtopic"])
                    subtopic_id = subtopic_cache[subtopic_key]

                    distractor_notes = Json(q["distractor_notes"]) if q.get("distractor_notes") else None
                    existing_id = get_existing_question_id(cur, subtopic_id, q["stem"])

                    if existing_id:
                        cur.execute(
                            """
                            update question set
                                difficulty = %s, format = %s, payload = %s, answer_key = %s,
                                explanation = %s, distractor_notes = %s
                            where id = %s
                            """,
                            (
                                q["difficulty"], q["format"], Json(q["payload"]), Json(q["answer_key"]),
                                q["explanation"], distractor_notes, existing_id,
                            ),
                        )
                        updated += 1
                        file_updated += 1
                    else:
                        cur.execute(
                            """
                            insert into question (
                                subtopic_id, difficulty, format, stem, payload, answer_key,
                                explanation, distractor_notes, status, source, generator_model
                            ) values (%s, %s, %s, %s, %s, %s, %s, %s, 'active', 'llm', %s)
                            """,
                            (
                                subtopic_id, q["difficulty"], q["format"], q["stem"],
                                Json(q["payload"]), Json(q["answer_key"]), q["explanation"],
                                distractor_notes, GENERATOR_MODEL,
                            ),
                        )
                        inserted += 1
                        file_inserted += 1

                print(f"{path.relative_to(QUESTIONS_DIR)}: {file_inserted} new, {file_updated} updated")
        conn.commit()

    print(f"\nTotal: inserted {inserted} new, updated {updated} existing questions.")


if __name__ == "__main__":
    main()
