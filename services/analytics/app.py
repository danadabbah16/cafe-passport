import os

import time

from flask import Flask, g, jsonify, request

from analytics import bp as analytics_bp
from budget import bp as budget_bp
from db import check_db, init_db

app = Flask(__name__)
init_db()
app.register_blueprint(analytics_bp)
app.register_blueprint(budget_bp)

UI_ORIGIN = os.environ.get("UI_ORIGIN", "http://localhost:8080")
VERSION = os.environ.get("GIT_SHA", "dev")


@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = UI_ORIGIN
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, OPTIONS"
    return resp

@app.before_request
def start_timer():
    g.start = time.perf_counter()


@app.after_request
def log_request(resp):
    ms = (time.perf_counter() - g.get("start", time.perf_counter())) * 1000
    print(f"{request.method} {request.path} {resp.status_code} {ms:.0f}ms", flush=True)
    return resp

@app.route("/health", methods=["GET"])
def health():
    # This service's own state only: never calls the other service.
    try:
        check_db()
        return jsonify({"status": "ok", "db": "ok", "version": VERSION}), 200
    except Exception:
        return jsonify({"status": "error", "db": "unavailable", "version": VERSION}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))