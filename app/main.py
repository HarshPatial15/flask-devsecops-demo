"""
DevSecOps demo Flask app.
Simulates a small task-management API with a health endpoint for smoke tests.
"""
import os
import sqlite3
import logging
from datetime import datetime
from flask import Flask, jsonify, request, g

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("task-api")

DB_PATH = os.environ.get("DB_PATH", "/tmp/tasks.db")
APP_VERSION = os.environ.get("APP_VERSION", "dev")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )"""
    )
    conn.commit()
    conn.close()


@app.route("/healthz", methods=["GET"])
def healthz():
    """Liveness/readiness probe + smoke test target."""
    try:
        db = get_db()
        db.execute("SELECT 1")
        return jsonify(status="ok", version=APP_VERSION), 200
    except Exception as e:
        logger.exception("Health check failed")
        return jsonify(status="error", detail=str(e)), 500


@app.route("/version", methods=["GET"])
def version():
    return jsonify(version=APP_VERSION), 200


@app.route("/tasks", methods=["GET"])
def list_tasks():
    db = get_db()
    rows = db.execute("SELECT id, title, done, created_at FROM tasks").fetchall()
    return jsonify([dict(r) for r in rows]), 200


@app.route("/tasks", methods=["POST"])
def create_task():
    payload = request.get_json(silent=True) or {}
    title = payload.get("title")
    if not title:
        return jsonify(error="title is required"), 400

    db = get_db()
    cur = db.execute(
        "INSERT INTO tasks (title, done, created_at) VALUES (?, ?, ?)",
        (title, 0, datetime.utcnow().isoformat()),
    )
    db.commit()
    return jsonify(id=cur.lastrowid, title=title, done=False), 201


@app.route("/tasks/<int:task_id>/complete", methods=["POST"])
def complete_task(task_id):
    db = get_db()
    db.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
    db.commit()
    return jsonify(id=task_id, done=True), 200


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
