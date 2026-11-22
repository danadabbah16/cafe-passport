import os

from flask import Flask, jsonify

from db import init_db, get_connection
from cafes import bp

app = Flask(__name__)
init_db()
app.register_blueprint(bp)

UI_ORIGIN = os.environ.get("UI_ORIGIN", "http://localhost:8080")


@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = UI_ORIGIN
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp

VERSION = os.environ.get("GIT_SHA", "dev")


@app.route("/health", methods=["GET"])
def health():
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()
        return jsonify({"status": "ok", "db": "ok", "version": VERSION}), 200
    except Exception:
        return jsonify({"status": "error", "db": "unreachable", "version": VERSION}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))