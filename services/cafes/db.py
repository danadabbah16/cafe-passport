import os
import sqlite3

DATA_DIR = os.environ.get("DATA_DIR", "./data")
DB_PATH = os.path.join(DATA_DIR, "cafe_passport.db")

SCHEMA = """
         CREATE TABLE IF NOT EXISTS cafes (
                                              id           INTEGER PRIMARY KEY AUTOINCREMENT,
                                              name         TEXT NOT NULL UNIQUE,
                                              neighborhood TEXT,
                                              city         TEXT NOT NULL,
                                              created_at   TEXT NOT NULL DEFAULT (datetime('now'))
             );

         CREATE TABLE IF NOT EXISTS visits (
                                               id         INTEGER PRIMARY KEY AUTOINCREMENT,
                                               cafe_id    INTEGER NOT NULL REFERENCES cafes(id),
             visit_date TEXT NOT NULL,
             drink      TEXT NOT NULL,
             price      REAL NOT NULL CHECK (price >= 0),
             rating     INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 10),
             notes      TEXT
             ); \
         """


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # rows behave like dicts: row["name"]
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite ignores FKs unless told not to
    return conn


def init_db():
    """Create schema if missing and seed starter data once. Safe to run on every boot."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = get_connection()
    conn.executescript(SCHEMA)
    _seed_if_empty(conn)
    conn.commit()
    conn.close()


def _seed_if_empty(conn):
    # only seed when the cafes table has no rows yet.
    count = conn.execute("SELECT COUNT(*) FROM cafes").fetchone()[0]
    if count > 0:
        return
    seed_path = os.path.join(os.path.dirname(__file__), "seed.sql")
    with open(seed_path, encoding="utf-8") as f:
        conn.executescript(f.read())