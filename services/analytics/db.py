import glob
import os
import time

import pymssql

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")
CONNECT_RETRIES = int(os.environ.get("DB_CONNECT_RETRIES", 8))


def parse_database_url(url: str) -> dict:
    """mssql://user:password@host:port/database -> pymssql connect arguments.
    Splits on the LAST '@', so the password may contain ':' '/' or '@'."""
    rest = url.split("://", 1)[1]
    creds, _, hostpart = rest.rpartition("@")
    user, _, password = creds.partition(":")
    hostport, _, database = hostpart.partition("/")
    host, _, port = hostport.partition(":")
    return {"server": host, "port": int(port or 1433),
            "user": user, "password": password, "database": database}


class Connection:
    """Thin wrapper so the rest of the code keeps the sqlite3-style API:
    conn.execute(sql, params) with '?' placeholders, rows as dicts."""

    def __init__(self, raw):
        self._raw = raw

    def execute(self, sql, params=()):
        cur = self._raw.cursor(as_dict=True)
        if params:
            cur.execute(sql.replace("?", "%s"), tuple(params))
        else:
            cur.execute(sql)
        return cur

    def commit(self):
        self._raw.commit()

    def close(self):
        self._raw.close()


def get_connection(retries: int = CONNECT_RETRIES) -> Connection:
    """Connect with retries and backoff: Azure SQL serverless may be paused
    and takes up to about a minute to resume."""
    cfg = parse_database_url(os.environ["DATABASE_URL"])
    delay = 1
    for attempt in range(1, retries + 1):
        try:
            return Connection(pymssql.connect(login_timeout=10, timeout=30, **cfg))
        except (pymssql.OperationalError, pymssql.InterfaceError) as e:
            if attempt == retries:
                raise
            print(f"db connect attempt {attempt}/{retries} failed ({type(e).__name__}); "
                  f"retrying in {delay}s", flush=True)
            time.sleep(delay)
            delay = min(delay * 2, 15)


def run_migrations(conn: Connection) -> None:
    """Apply migrations/NNN_*.sql in order, each exactly once,
    recording applied files in schema_migrations."""
    conn.execute(
        "IF OBJECT_ID('schema_migrations', 'U') IS NULL "
        "CREATE TABLE schema_migrations ("
        " version NVARCHAR(255) NOT NULL PRIMARY KEY,"
        " applied_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME())"
    )
    conn.commit()
    applied = {r["version"] for r in conn.execute("SELECT version FROM schema_migrations").fetchall()}
    for path in sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql"))):
        version = os.path.basename(path)
        if version in applied:
            continue
        print(f"applying migration {version}", flush=True)
        with open(path, encoding="utf-8") as f:
            conn.execute(f.read())
        conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
        conn.commit()
        print(f"applied migration {version}", flush=True)


def init_db() -> None:
    """Run pending migrations. Analytics has no seed data."""
    conn = get_connection()
    run_migrations(conn)
    conn.commit()
    conn.close()
