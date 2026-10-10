import os
from datetime import date, datetime

from flask import Blueprint, jsonify

from db import get_connection

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


# routes (thin: fetch rows, call the math)

@bp.route("/rankings", methods=["GET"])
def rankings():
    conn = get_connection()
    rows = conn.execute(
        "SELECT c.name AS cafe_name, v.visit_date, v.rating "
        "FROM visits v JOIN cafes c ON c.id = v.cafe_id"
    ).fetchall()
    conn.close()

    visits_by_cafe = {}
    for row in rows:
        visits_by_cafe.setdefault(row["cafe_name"], []).append(
            {"visit_date": row["visit_date"], "rating": row["rating"]}
        )
    return jsonify(rank_cafes(visits_by_cafe, date.today()))


@bp.route("/stats", methods=["GET"])
def stats():
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS n, SUM(price) AS spent, AVG(rating) AS avg_rating FROM visits"
    ).fetchone()
    top = conn.execute(
        "SELECT c.name, COUNT(*) AS n FROM visits v JOIN cafes c ON c.id = v.cafe_id "
        "GROUP BY c.id ORDER BY n DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return jsonify({
        "total_visits": row["n"],
        "total_spent": round(row["spent"], 2) if row["spent"] else 0,
        "average_rating": round(row["avg_rating"], 2) if row["avg_rating"] else None,
        "most_visited": top["name"] if top else None,
    })