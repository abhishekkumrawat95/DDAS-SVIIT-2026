"""
DDAS – Database Initialization
Creates the SQLite schema for downloads, alerts, and configurations.
"""

import sqlite3
import os
import sys

# Resolve the canonical DB path from db_helper
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.db_helper import DB_PATH, get_connection


SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS downloads (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name        TEXT    NOT NULL,
    file_hash        TEXT    UNIQUE NOT NULL,
    file_path        TEXT    NOT NULL,
    file_type        TEXT,
    file_size        INTEGER,
    extracted_text   TEXT,
    image_phash      TEXT,
    video_fingerprint TEXT,
    downloaded_by    TEXT    DEFAULT 'unknown',
    download_time    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_for       TEXT    NOT NULL,
    duplicate_type  TEXT    NOT NULL,
    similarity      REAL    DEFAULT 0.0,
    new_file_name   TEXT,
    new_file_path   TEXT,
    original_file   TEXT,
    original_path   TEXT,
    original_user   TEXT,
    original_time   TEXT,
    status          TEXT    DEFAULT 'pending',
    created_at      TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS configurations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key  TEXT UNIQUE NOT NULL,
    config_value TEXT,
    modified_at TEXT DEFAULT (datetime('now'))
);

-- Default configuration values
INSERT OR IGNORE INTO configurations (config_key, config_value)
VALUES
    ('monitor_interval', '5'),
    ('text_similarity_threshold', '0.75'),
    ('image_similarity_threshold', '10'),
    ('admin_email', ''),
    ('slack_webhook', ''),
    ('monitored_folders', '');
"""


def init_database():
    """Create all tables and insert default configuration."""
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)

    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.close()
    print(f"[DB] Database initialised at: {DB_PATH}")


if __name__ == "__main__":
    init_database()
