"""Load hand-written "Learn First" reading content into the database.

Run manually: python scripts/load_readings.py

Content lives as Markdown under content/readings/ (one file per area). The
first line must be "# Area Name"; each subsequent "## Topic Name" heading
starts that topic's reading, running until the next "## " heading or the
end of file. Upserts by topic_id -- re-running after editing a file
updates the existing reading in place.

Runs outside the Streamlit runtime, so it reads the DB URI straight from
secrets.toml rather than going through lib/db/client.py.
"""

import pathlib
import re
import sys
import tomllib

import psycopg

ROOT = pathlib.Path(__file__).resolve().parent.parent
READINGS_DIR = ROOT / "content" / "readings"
SECRETS_PATH = ROOT / ".streamlit" / "secrets.toml"
GENERATOR_MODEL = "claude-sonnet-5"

_SECTION_RE = re.compile(r"^## (.+)$", re.MULTILINE)


def load_db_uri() -> str:
    if not SECRETS_PATH.exists():
        sys.exit(f"Missing {SECRETS_PATH}. Copy .streamlit/secrets.toml.example and fill it in first.")
    with open(SECRETS_PATH, "rb") as f:
        secrets = tomllib.load(f)
    try:
        return secrets["supabase"]["db_uri"]
    except KeyError:
        sys.exit("secrets.toml is missing [supabase] db_uri.")


def parse_readings_file(path: pathlib.Path) -> tuple[str, dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        sys.exit(f"{path.name}: first line must be '# Area Name'")
    area_name = lines[0][2:].strip()
    body = "\n".join(lines[1:])

    parts = _SECTION_RE.split(body)
    if len(parts) < 3:
        sys.exit(f"{path.name}: no '## Topic Name' sections found")

    readings = {}
    for i in range(1, len(parts), 2):
        topic_name = parts[i].strip()
        content = parts[i + 1].strip()
        readings[topic_name] = content
    return area_name, readings


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


def main() -> None:
    db_uri = load_db_uri()
    files = sorted(READINGS_DIR.glob("*.md"))
    if not files:
        print(f"No reading files found under {READINGS_DIR}.")
        return

    inserted = updated = 0
    # prepare_threshold=None: the Supabase transaction pooler doesn't support
    # server-side prepared statements persisting across pooled connections.
    with psycopg.connect(db_uri, autocommit=False, prepare_threshold=None) as conn:
        with conn.cursor() as cur:
            for path in files:
                area_name, readings = parse_readings_file(path)
                area_id = get_area_id(cur, area_name)
                file_inserted = file_updated = 0

                for topic_name, content in readings.items():
                    topic_id = get_topic_id(cur, area_id, topic_name)
                    cur.execute(
                        """
                        insert into reading (topic_id, content, source, generator_model)
                        values (%s, %s, 'llm', %s)
                        on conflict (topic_id) do update set
                            content = excluded.content,
                            generator_model = excluded.generator_model,
                            updated_at = now()
                        returning (xmax = 0) as was_insert
                        """,
                        (topic_id, content, GENERATOR_MODEL),
                    )
                    was_insert = cur.fetchone()[0]
                    if was_insert:
                        inserted += 1
                        file_inserted += 1
                    else:
                        updated += 1
                        file_updated += 1

                print(f"{path.name}: {file_inserted} new, {file_updated} updated")
        conn.commit()

    print(f"\nTotal: inserted {inserted} new, updated {updated} existing readings.")


if __name__ == "__main__":
    main()
