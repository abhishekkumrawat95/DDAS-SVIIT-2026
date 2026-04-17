"""
DDAS – Database initialization
Creates tables if they do not already exist.
"""

import sqlite3
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS downloads (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name        TEXT    NOT NULL,
    file_hash        TEXT    NOT NULL UNIQUE,
    file_path        TEXT    NOT NULL,
    file_type        TEXT,
    file_size        INTEGER,
    extracted_text   TEXT,
    image_phash      TEXT,
    video_fingerprint TEXT,
    downloaded_by    TEXT,
    download_time    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_for       TEXT    NOT NULL,
    duplicate_type  TEXT    NOT NULL,
    similarity      REAL    NOT NULL DEFAULT 1.0,
    new_file_name   TEXT,
    new_file_path   TEXT,
    original_file   TEXT,
    original_path   TEXT,
    original_user   TEXT,
    original_time   TEXT,
    status          TEXT    NOT NULL DEFAULT 'pending',
    created_time    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_downloads_hash  ON downloads(file_hash);
CREATE INDEX IF NOT EXISTS idx_downloads_user  ON downloads(downloaded_by);
CREATE INDEX IF NOT EXISTS idx_alerts_user     ON alerts(alert_for);
CREATE INDEX IF NOT EXISTS idx_alerts_status   ON alerts(status);
"""


def init_db(db_path: str = DB_PATH) -> None:
    """Create tables and indexes if they don't exist."""
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"[init_db] Database ready at {db_path}")


if __name__ == "__main__":
    init_db()
