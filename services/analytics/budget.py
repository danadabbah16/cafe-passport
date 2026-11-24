from flask import Blueprint, jsonify, request

from db import get_connection

bp = Blueprint("budget", __name__)


@bp.route("/budget", methods=["GET"])
def get_budget():
    conn = get_connection()
    row = conn.execute("SELECT monthly_goal FROM budget_goal WHERE id = 1").fetchone()
    conn.close()
    return jsonify({"monthly_goal": row["monthly_goal"] if row else None})


@bp.route("/budget", methods=["PUT"])
def set_budget():
    data = request.get_json(silent=True) or {}
    try:
        goal = float(data.get("monthly_goal"))
    except (TypeError, ValueError):
        return jsonify({"error": "monthly_goal must be a number"}), 400
    if goal <= 0:
        return jsonify({"error": "monthly_goal must be greater than 0"}), 400

    conn = get_connection()
    cur = conn.execute(
        "UPDATE budget_goal SET monthly_goal = ?, updated_at = SYSUTCDATETIME() WHERE id = 1",
        (goal,),
    )
    if cur.rowcount == 0:
        conn.execute("INSERT INTO budget_goal (id, monthly_goal) VALUES (1, ?)", (goal,))
    conn.commit()
    conn.close()
    return jsonify({"monthly_goal": goal}), 200