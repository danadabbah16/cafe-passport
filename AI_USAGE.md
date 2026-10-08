# AI Usage Log

| Date/commit | Tool | Prompt | Disposition | What changed & why (if modified) | In my own words, how this works |
|---|---|---|---|---|---|
| 2026-10-08 | Claude | Help setting up a basic Flask app that meets the container contract | Modified | app.py reads PORT and DATA_DIR from environment variables with defaults, creates the data folder, and runs Flask on 0.0.0.0 so it is reachable from inside a container. /health returns a simple JSON status so you can check the app is alive. |
| 2026-10-08 | Claude | Help designing the SQLite schema and an idempotent init with seed data | Modified | Adjusted seed.sql to cafes I actually visit; decided rankings are computed on demand instead of stored (ADR-2) | db.py defines two tables (cafes, visits) and init_db() runs CREATE TABLE IF NOT EXISTS so existing tables are untouched, then counts rows in cafes and only loads seed.sql when the count is zero, so restarting the app never duplicates seed data. |