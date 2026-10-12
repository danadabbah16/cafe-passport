# Café Passport

A personal café visit log with a ranking engine. Two domains: a visit-logging
API (`cafes.py`) and an analytics engine (`analytics.py`) that computes
recency-weighted, confidence-adjusted café rankings from raw visit history.

## Run locally

    git clone https://github.com/danadabbah16/cafe-passport
    cd cafe-passport
    python -m venv .venv
    .venv\Scripts\activate          # Windows; on Unix: source .venv/bin/activate
    python -m pip install -r requirements.txt
    python app.py

Open http://localhost:8000/ for the dashboard.

## Run with Docker

    docker build -t cafe-passport .
    docker run -p 8000:8000 -v cafe-data:/data cafe-passport

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| PORT | 8000 | HTTP port the app listens on |
| DATA_DIR | ./data (container: /data) | Directory for the SQLite file |
| HALF_LIFE_DAYS | 60 | Days until a visit's ranking weight halves |
| CONFIDENCE_K | 3 | Shrinkage constant toward the global mean |

SQLite path: `<DATA_DIR>/cafe_passport.db`. Schema is created and seed data
(`seed.sql`) loaded on first boot only when the cafes table is empty.

## API

| Route | Method | Purpose |
|---|---|---|
| / | GET | HTML dashboard |
| /health | GET | Liveness check |
| /cafes | GET / POST | List / create cafés |
| /cafes/<id>/visits | GET / POST | List / log visits for a café |
| /rankings | GET | Recency-weighted, confidence-adjusted ranking |
| /stats | GET | Totals: visits, spend, average rating, most visited |

## Tests & coverage (§4)

    python -m pytest --cov=app --cov=db --cov=cafes --cov=analytics --cov-report=term-missing

```
(.venv) C:\Users\ddabb\Documents\cafe-passport>python -m pytest --cov=app --cov=db --cov=cafes --cov=analytics --cov-report=term-missing
======================================================= test session starts ========================================================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\ddabb\Documents\cafe-passport
plugins: cov-7.1.0
collected 17 items

tests\test_analytics.py .........                                                                                             [ 52%]
tests\test_cafes.py ........                                                                                                  [100%]

========================================================== tests coverage ==========================================================
_________________________________________ coverage: platform win32, python 3.14.7-final-0 __________________________________________

Name           Stmts   Miss  Cover   Missing
--------------------------------------------
analytics.py      49      5    90%   83-92
app.py            19      3    84%   23, 27-29
cafes.py          59      9    85%   10-13, 52-54, 62-63
db.py             24      1    96%   49
--------------------------------------------
TOTAL            151     18    88%
======================================================== 17 passed in 0.21s ========================================================
```

## Container contract evidence (§7)

    ./container/run.sh /path/to/repo

```
=== SDD Assignment 1 contract check ===
Repository: /mnt/c/Users/ddabb/Documents/cafe-passport

==> Repository shape
  PASS  one Dockerfile, one manifest (requirements.txt)

==> Build from a clean context, no build args
  PASS  image built
  PASS  image size 219 MB

==> Start on PORT=8000 and reach it from the host
  PASS  HTTP 200 from http://localhost:8000/

==> SQLite file under DATA_DIR
  PASS  found in /data: cafe_passport.db

==> Data persists, and a second boot does not re-seed
  PASS  volume at /data persists
  PASS  row counts unchanged across restart: cafes=4 visits=0

==> PORT override is honoured (not hardcoded)
  PASS  HTTP 200 from http://localhost:9123/

=== ALL CHECKS PASSED ===
Paste this output into your README as the §7 evidence.

```
