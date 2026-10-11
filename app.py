import os

from flask import Flask, jsonify
from db import init_db
from cafes import bp as cafes_bp
from analytics import bp as analytics_bp


app = Flask(__name__)

init_db()  # create schema + seed on first boot
app.register_blueprint(cafes_bp)
app.register_blueprint(analytics_bp)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/")
def index():
    return jsonify({
        "app": "cafe-passport",
        "endpoints": ["/health", "/cafes", "/cafes/<id>/visits", "/rankings", "/stats"],
    })


if __name__ == "__main__":
    # Port from environment with a sane default (container contract)
    port = int(os.environ.get("PORT", 8000))
    # Bind 0.0.0.0, not localhost — otherwise unreachable from outside a container
    app.run(host="0.0.0.0", port=port)