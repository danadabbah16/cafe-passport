# Architecture Decision Records

## 1. Backend framework: Flask with stdlib sqlite3
Date: 2026-10-08
Status: Decided
Context: Single-process monolith with two domains (visit logging, ranking analytics) over HTTP with SQLite. The stack must stay small enough to explain line-by-line at the comprehension check.
Decision: Flask for routing/JSON, Python's built-in sqlite3 for persistence, no ORM.
Alternatives considered: FastAPI — async and auto-docs add nothing for a single-user app with no concurrent I/O; Django — brings ORM/admin/auth machinery this project doesn't need, which the brief itself cites as poor judgment at this scale.
Consequences: Minimal dependencies and full control over SQL (which I need for the analytics queries); I hand-write DB access, acceptable at this size.

## 2. Data model: two tables, rankings computed on demand
Date: 2026-10-09
Status: Decided
Context: The analytics domain needs cafe scores derived from visits; I had to decide whether scores live in the database or are computed per request.
Decision: Only `cafes` and `visits` are stored (visits reference cafes by id). All rankings and stats are computed on the fly from visit rows.
Alternatives considered: A `scores` table updated on each new visit — rejected because it can go stale, needs sync logic, and brings no benefit at single-user data volumes.
Consequences: Analytics is always correct with zero sync code; every ranking request re-reads visits, which is fine at this scale but would need caching if the data grew large.

## 3. Ranking algorithm: exponential recency decay + confidence shrinkage
Date: 2026-10-10
Status: Decided
Context: A plain average rating treats a visit from six months ago the same as yesterday's, and lets a single lucky 10/10 visit outrank a consistently good regular spot.
Decision: Each visit's weight halves every HALF_LIFE_DAYS (default 60, env-configurable); the weighted score is then shrunk toward the global mean with constant k=3, so low-visit cafes can't dominate. Cafes with zero visits are excluded from rankings.
Alternatives considered: Plain mean rating — rejected because taste changes and sample sizes vary wildly; a stored score column — already rejected in ADR-2.
Consequences: Rankings reflect recent experience and are robust to small samples; two extra parameters (half-life, k) must be justified and documented in the README.

## 4. Testing approach: pure functions first, API validation second
Date: 2026-10-11
Status: Decided
Context: The 70% bar should be spent on logic that can actually be wrong, not framework glue.
Decision: Unit-test the ranking math (weights, weighted score, shrinkage, ordering) against hand-computed values, and the API's validation rules (404/400/409 paths) through Flask's test client on a temp database.
Alternatives considered: End-to-end tests against a running server with curl-style calls — rejected as slower, flakier, and no better at catching logic errors.
Consequences: High confidence in the math and input handling.

## 5. Deliberately not built: multi-user accounts and authentication
Date: 2026-10-12
Status: Decided
Context: A visit log could naturally serve many users, which would require accounts, login, and per-user data separation.
Decision: The app is single-user by design: no auth, no user table, every visit belongs to the one owner.
Alternatives considered: Flask-Login with a users table — rejected because it adds a dependency and schema complexity that serve no requirement in this assignment, and §1b asks that additions be justified.
Consequences: The app stays small and fully explainable; multi-user support would require adding a user_id to visits and an auth layer, which is feasible later without touching the ranking logic.

## ADR-6: Splitting the monolith along the logging/analytics seam
Date: 2026-11-20
Status: Accepted

**Context:** Assignment 2 requires one service per feature domain, each with its own container and its own database. ADR-2 placed the seam between logging (cafes, visits) and analytics (rankings, stats), with analytics only reading visit rows.

**Decision:** Split into two services:
- `cafes` (services/cafes): owns the `cafes` and `visits` tables; exposes POST/GET /cafes, POST/GET /cafes/{id}/visits, and a new GET /visits returning all visit rows (cafe_id, visit_date, rating, price).
- `analytics` (services/analytics): owns its own database holding the monthly budget goal (moved from browser localStorage, giving the domain real state); computes /rankings and /stats by calling GET /visits on cafes over HTTP, using CAFES_URL from the environment.

The cross-seam flow is server side: analytics → cafes. A single GET /visits call replaces one call per café, so rankings cost one HTTP request rather than N.

**Alternatives considered:** UI calling both services and computing rankings in the browser (rejected: moves domain logic into the UI); analytics keeping a copy of visits synced from cafes (rejected: needs a message broker or background job, both out of scope).

**Consequences:** ADR-2 held: only read access to visit rows crosses the seam. Analytics can no longer join visits to café names in SQL; it joins in code after one call. If cafes is down, analytics cannot rank (handled in a later ADR on partial failure); cafes is unaffected by analytics being down.