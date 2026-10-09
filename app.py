import os

from flask import Flask, jsonify
from db import init_db
from cafes import bp as cafes_bp


app = Flask(__name__)

init_db()  # create schema + seed on first boot
app.register_blueprint(cafes_bp)

# Data directory is configurable so a container can mount a volume here (container contract)
DATA_DIR = os.environ.get("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "cafe_passport.db")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # Port from environment with a sane default (container contract)
    port = int(os.environ.get("PORT", 8000))
    # Bind 0.0.0.0, not localhost — otherwise unreachable from outside a container
    app.run(host="0.0.0.0", port=port)