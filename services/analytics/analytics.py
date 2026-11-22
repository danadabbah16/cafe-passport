import os
from datetime import date, datetime

from collections import Counter

from flask import Blueprint, jsonify

import json
import urllib.error
import urllib.request

bp = Blueprint("analytics", __name__)

# Tunable parameters (env-overridable, sane defaults)
HALF_LIFE_DAYS = float(os.environ.get("HALF_LIFE_DAYS", 60))
CONFIDENCE_K = float(os.environ.get("CONFIDENCE_K", 3))


# pure functions (no database, fully testable)

def recency_weight(visit_date: str, today: date, half_life: float = HALF_LIFE_DAYS) -> float:
    """Weight of a visit: 1.0 today, 0.5 at half_life days old, 0.25 at double, etc."""
    d = datetime.strptime(visit_date, "%Y-%m-%d").date()
    days_ago = max((today - d).days, 0)
    return 0.5 ** (days_ago / half_life)


def weighted_score(visits: list, today: date) -> float:
    """Recency-weighted average rating of one cafe's visits."""
    total_weight = 0.0
    total = 0.0
    for v in visits:
        w = recency_weight(v["visit_date"], today)
        total += v["rating"] * w
        total_weight += w
    return total / total_weight if total_weight > 0 else 0.0


def adjusted_score(score: float, n_visits: int, global_mean: float, k: float = CONFIDENCE_K) -> float:
    """Shrink low-sample scores toward the global mean (IMDb-style).
    With many visits the score dominates; with few, the global mean does."""
    return (n_visits * score + k * global_mean) / (n_visits + k)


def rank_cafes(visits_by_cafe: dict, today: date) -> list:
    """visits_by_cafe: {cafe_name: [visit rows]} -> ranked list of dicts, best first."""
    all_ratings = [v["rating"] for vs in visits_by_cafe.values() for v in vs]
    if not all_ratings:
        return []
    global_mean = sum(all_ratings) / len(all_ratings)

    results = []
    for cafe_name, vs in visits_by_cafe.items():
        raw = weighted_score(vs, today)
        adj = adjusted_score(raw, len(vs), global_mean)
        results.append({
            "cafe": cafe_name,
            "score": round(adj, 2),
            "raw_score": round(raw, 2),
            "visits": len(vs),
        })
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


# data access: the ONLY place analytics reads data it does not own.
# After the split these two functions become HTTP calls to the cafes service
# (GET /visits and GET /cafes); nothing below them changes.

# data access: the ONLY place analytics reads data it does not own.
# Both calls go to the cafes service over HTTP, with a timeout.

CAFES_URL = os.environ.get("CAFES_URL", "http://cafes:8000").rstrip("/")
CAFES_TIMEOUT_S = float(os.environ.get("CAFES_TIMEOUT_S", 2))


class CafesUnavailable(Exception):
    """The cafes service could not be reached, timed out, or returned bad data."""


def _get_json(path: str):
    try:
        with urllib.request.urlopen(f"{CAFES_URL}{path}", timeout=CAFES_TIMEOUT_S) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        raise CafesUnavailable(str(e)) from e


def load_visits() -> list:
    """All visit rows, from GET /visits on the cafes service."""
    return _get_json("/visits")


def load_cafe_names() -> dict:
    """{cafe_id: name}, from GET /cafes on the cafes service."""
    return {c["id"]: c["name"] for c in _get_json("/cafes")}


@bp.errorhandler(CafesUnavailable)
def cafes_unavailable(e):
    return jsonify({
        "error": "cafes service unavailable",
        "detail": "Rankings and stats need visit data from the cafes service. Try again shortly.",
    }), 503


# joins in code (previously SQL JOINs)

def group_by_cafe(visits: list, names: dict) -> dict:
    """{cafe_name: [visit rows]}. Visits whose cafe_id has no cafe are skipped,
    matching the old inner JOIN."""
    grouped = {}
    for v in visits:
        name = names.get(v["cafe_id"])
        if name is None:
            continue
        grouped.setdefault(name, []).append(
            {"visit_date": v["visit_date"], "rating": v["rating"]}
        )
    return grouped


def compute_stats(visits: list, names: dict) -> dict:
    """Totals across all visits, plus the most visited cafe."""
    n = len(visits)
    spent = sum(v["price"] for v in visits)
    counts = Counter(v["cafe_id"] for v in visits if v["cafe_id"] in names)
    top = counts.most_common(1)
    return {
        "total_visits": n,
        "total_spent": round(spent, 2) if spent else 0,
        "average_rating": round(sum(v["rating"] for v in visits) / n, 2) if n else None,
        "most_visited": names[top[0][0]] if top else None,
    }


# routes (thin: load data, call the logic)

@bp.route("/rankings", methods=["GET"])
def rankings():
    visits_by_cafe = group_by_cafe(load_visits(), load_cafe_names())
    return jsonify(rank_cafes(visits_by_cafe, date.today()))


@bp.route("/stats", methods=["GET"])
def stats():
    return jsonify(compute_stats(load_visits(), load_cafe_names()))