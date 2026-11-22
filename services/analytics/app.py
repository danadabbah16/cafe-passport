import os

from flask import Flask, jsonify

from analytics import bp

app = Flask(__name__)
app.register_blueprint(bp)

VERSION = os.environ.get("GIT_SHA", "dev")


@app.route("/health", methods=["GET"])
def health():
    # Reports this service's own state only, never the cafes service's.
    # Database check is added when analytics gets its own database.
    return jsonify({"status": "ok", "version": VERSION}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))