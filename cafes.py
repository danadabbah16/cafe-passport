from flask import Blueprint, jsonify, request

from db import get_connection

bp = Blueprint("cafes", __name__)


@bp.route("/cafes", methods=["GET"])
def list_cafes():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM cafes ORDER BY name").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@bp.route("/cafes", methods=["POST"])
def add_cafe():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    city = (data.get("city") or "").strip()
    if not name or not city:
        return jsonify({"error": "name and city are required"}), 400

    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO cafes (name, neighborhood, city) VALUES (?, ?, ?)",
            (name, data.get("neighborhood"), city),
        )
        conn.commit()
        new_id = cur.lastrowid
    except Exception:
        conn.close()
        return jsonify({"error": "cafe with this name already exists"}), 409
    conn.close()
    return jsonify({"id": new_id, "name": name}), 201


@bp.route("/cafes/<int:cafe_id>/visits", methods=["POST"])
def log_visit(cafe_id):
    data = request.get_json(silent=True) or {}

    conn = get_connection()
    cafe = conn.execute("SELECT id FROM cafes WHERE id = ?", (cafe_id,)).fetchone()
    if cafe is None:
        conn.close()
        return jsonify({"error": "cafe not found"}), 404   # the decision from the homework

    try:
        rating = int(data.get("rating"))
        price = float(data.get("price"))
    except (TypeError, ValueError):
        conn.close()
        return jsonify({"error": "rating and price must be numbers"}), 400
    if not (1 <= rating <= 10):
        conn.close()
        return jsonify({"error": "rating must be between 1 and 10"}), 400

    visit_date = data.get("visit_date")
    drink = (data.get("drink") or "").strip()
    if not visit_date or not drink:
        conn.close()
        return jsonify({"error": "visit_date and drink are required"}), 400

    cur = conn.execute(
        "INSERT INTO visits (cafe_id, visit_date, drink, price, rating, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (cafe_id, visit_date, drink, price, rating, data.get("notes")),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({"id": new_id, "cafe_id": cafe_id}), 201


@bp.route("/cafes/<int:cafe_id>/visits", methods=["GET"])
def list_visits(cafe_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM visits WHERE cafe_id = ? ORDER BY visit_date DESC",
        (cafe_id,),
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])