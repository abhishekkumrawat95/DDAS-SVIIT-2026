"""
DDAS database initialisation – creates all tables on first run.

Usage:
    python db/init_db.py
"""

import sqlite3
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config


def init_database(db_path: str = config.DB_PATH) -> None:
    """Create the DDAS SQLite database and all required tables."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # ── downloads ─────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS downloads (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name         TEXT    NOT NULL,
            file_hash         TEXT    NOT NULL UNIQUE,
            file_path         TEXT    NOT NULL,
            file_type         TEXT,
            file_size         INTEGER,
            extracted_text    TEXT,
            image_phash       TEXT,
            video_fingerprint TEXT,
            downloaded_by     TEXT    NOT NULL,
            download_time     TEXT    NOT NULL,
            created_at        TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── alerts ────────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_for       TEXT    NOT NULL,
            duplicate_type  TEXT    NOT NULL,
            similarity      REAL    DEFAULT 100.0,
            new_file_name   TEXT    NOT NULL,
            new_file_path   TEXT    NOT NULL,
            original_file   TEXT    NOT NULL,
            original_path   TEXT    NOT NULL,
            original_user   TEXT    NOT NULL,
            original_time   TEXT    NOT NULL,
            status          TEXT    DEFAULT 'pending',
            created_at      TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── users ─────────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL UNIQUE,
            email      TEXT,
            role       TEXT DEFAULT 'user',
            created_at TEXT DEFAULT (datetime('now')),
            last_login TEXT
        )
    """)

    # ── monitored_folders ─────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS monitored_folders (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_path   TEXT NOT NULL UNIQUE,
            folder_name   TEXT,
            scan_interval INTEGER DEFAULT 5,
            status        TEXT    DEFAULT 'active',
            created_by    TEXT,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── chat_history ──────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL,
            query      TEXT NOT NULL,
            response   TEXT NOT NULL,
            source     TEXT DEFAULT 'local',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()
    print(f"[DDAS] Database initialised at: {db_path}")


if __name__ == "__main__":
    init_database()
