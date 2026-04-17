"""
DDAS – REST API Server
Provides a Flask-based REST API for the web dashboard and external integrations.

Usage:
    python api_server.py
    python api_server.py --host 0.0.0.0 --port 5000
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db import init_db, db_helper
from chatbot import chatbot_engine
import config

try:
    from flask import Flask, jsonify, request, abort
    _FLASK_AVAILABLE = True
except ImportError:
    _FLASK_AVAILABLE = False

app = Flask(__name__) if _FLASK_AVAILABLE else None


# ── Helper ────────────────────────────────────────────────────────────────────

def _require_flask():
    if not _FLASK_AVAILABLE:
        print("[DDAS API] Flask is not installed. Run: pip install flask")
        sys.exit(1)


# ── Routes ────────────────────────────────────────────────────────────────────

if _FLASK_AVAILABLE:

    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "ok", "service": "DDAS API"})

    @app.route("/api/downloads", methods=["GET"])
    def get_downloads():
        """Return all download records."""
        rows = db_helper.get_all_downloads()
        data = [
            {
                "file_name": r[0],
                "file_type": r[1],
                "downloaded_by": r[2],
                "download_time": r[3],
                "file_path": r[4],
            }
            for r in rows
        ]
        return jsonify(data)

    @app.route("/api/alerts", methods=["GET"])
    def get_alerts():
        """Return pending alerts, optionally filtered by username."""
        username = request.args.get("user")
        import sqlite3
        conn = sqlite3.connect(config.DB_PATH)
        if username:
            rows = conn.execute(
                "SELECT * FROM alerts WHERE alert_for = ? AND status = 'pending'",
                (username,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM alerts ORDER BY id DESC").fetchall()
        conn.close()
        columns = [
            "id", "alert_for", "duplicate_type", "similarity",
            "new_file_name", "new_file_path", "original_file",
            "original_path", "original_user", "original_time",
            "status", "created_at",
        ]
        return jsonify([dict(zip(columns, r)) for r in rows])

    @app.route("/api/alerts/<int:alert_id>", methods=["PATCH"])
    def update_alert(alert_id: int):
        """Update the status of an alert (e.g., mark as resolved)."""
        body = request.get_json(silent=True) or {}
        status = body.get("status", "resolved")
        allowed = {"pending", "shown", "resolved"}
        if status not in allowed:
            abort(400, description=f"status must be one of {allowed}")
        db_helper.update_alert_status(alert_id, status)
        return jsonify({"id": alert_id, "status": status})

    @app.route("/api/chatbot", methods=["POST"])
    def chatbot():
        """
        Query the DDAS chatbot.

        Request body (JSON):
            { "query": "...", "username": "..." }

        Response:
            { "query": "...", "local_results": [...], "online_results": [...], "summary": "..." }
        """
        body = request.get_json(silent=True) or {}
        query = (body.get("query") or "").strip()
        if not query:
            abort(400, description="'query' field is required")
        username = body.get("username", "api_user")
        result = chatbot_engine.ask(query, username=username)
        return jsonify(result)

    @app.route("/api/stats", methods=["GET"])
    def stats():
        """Return summary statistics."""
        import sqlite3
        conn = sqlite3.connect(config.DB_PATH)
        total_downloads = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
        total_alerts = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        pending_alerts = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE status='pending'"
        ).fetchone()[0]
        conn.close()
        return jsonify({
            "total_downloads": total_downloads,
            "total_alerts": total_alerts,
            "pending_alerts": pending_alerts,
        })


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    _require_flask()
    parser = argparse.ArgumentParser(description="DDAS REST API Server")
    parser.add_argument("--host", default=config.API_HOST, help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=config.API_PORT, help="Bind port (default: 5000)")
    parser.add_argument("--debug", action="store_true", default=config.API_DEBUG)
    args = parser.parse_args()

    init_db.init_database()
    print(f"[DDAS API] Starting on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
