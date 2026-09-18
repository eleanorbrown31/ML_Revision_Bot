"""Apply pending SQL migrations under /migrations, in filename order.

Run manually: python scripts/apply_migrations.py
Reads the Supabase connection string from .streamlit/secrets.toml (the same
file the app uses), since this script runs outside the Streamlit runtime.
"""

import pathlib
import sys
import tomllib

import psycopg

ROOT = pathlib.Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = ROOT / "migrations"
SECRETS_PATH = ROOT / ".streamlit" / "secrets.toml"


def load_db_uri() -> str:
    if not SECRETS_PATH.exists():
        sys.exit(f"Missing {SECRETS_PATH}. Copy .streamlit/secrets.toml.example and fill it in first.")
    with open(SECRETS_PATH, "rb") as f:
        secrets = tomllib.load(f)
    try:
        return secrets["supabase"]["db_uri"]
    except KeyError:
        sys.exit("secrets.toml is missing [supabase] db_uri.")


def main() -> None:
    db_uri = load_db_uri()
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print("No migration files found.")
        return

    bootstrap_path = MIGRATIONS_DIR / "000_bootstrap.sql"
    if not bootstrap_path.exists():
        sys.exit("Missing migrations/000_bootstrap.sql")

    # prepare_threshold=None: the Supabase transaction pooler doesn't support
    # server-side prepared statements persisting across pooled connections.
    with psycopg.connect(db_uri, autocommit=False, prepare_threshold=None) as conn:
        # Bootstrap creates schema_migrations itself and is idempotent, so it
        # always runs; everything after it is tracked and skipped once applied.
        with conn.cursor() as cur:
            cur.execute(bootstrap_path.read_text())
            cur.execute(
                "insert into schema_migrations (filename) values (%s) on conflict do nothing",
                (bootstrap_path.name,),
            )
        conn.commit()

        for path in migration_files:
            if path.name == bootstrap_path.name:
                continue
            with conn.cursor() as cur:
                cur.execute("select 1 from schema_migrations where filename = %s", (path.name,))
                if cur.fetchone():
                    print(f"skip  {path.name} (already applied)")
                    continue
                print(f"apply {path.name}")
                cur.execute(path.read_text())
                cur.execute(
                    "insert into schema_migrations (filename) values (%s)",
                    (path.name,),
                )
            conn.commit()

    print("Migrations up to date.")


if __name__ == "__main__":
    main()
