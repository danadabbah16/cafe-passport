# Architecture Decision Records

## 1. Backend framework: Flask with stdlib sqlite3
Date: 2026-10-08

Status: Decided

Context: Single-process monolith with two domains (visit logging, ranking analytics) over HTTP with SQLite. The stack must stay small enough to explain line-by-line at the comprehension check.
Decision: Flask for routing/JSON, Python's built-in sqlite3 for persistence, no ORM.

Alternatives considered: FastAPI — async and auto-docs add nothing for a single-user app with no concurrent I/O; Django — brings ORM/admin/auth machinery this project doesn't need, which the brief itself cites as poor judgment at this scale.

Consequences: Minimal dependencies and full control over SQL (which I need for the analytics queries); I hand-write DB access, acceptable at this size.