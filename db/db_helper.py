"""
DDAS – Database helper
All CRUD operations for the downloads and alerts tables.
"""

import sqlite3
import os
import sys
from datetime import datetime
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DB_PATH


# ── Connection ────────────────────────────────────────────────────────────────

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Return a WAL-mode SQLite connection."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


# ── Downloads ─────────────────────────────────────────────────────────────────

def insert_download(
    file_name: str,
    file_hash: str,
    file_path: str,
    file_type: str,
    file_size: int,
    downloaded_by: str,
    extracted_text: Optional[str] = None,
    image_phash: Optional[str] = None,
    video_fingerprint: Optional[str] = None,
) -> bool:
    """
    Insert a new download record.

    Returns True on success, False if the hash already exists (duplicate).
    """
    try:
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO downloads
                (file_name, file_hash, file_path, file_type, file_size,
                 extracted_text, image_phash, video_fingerprint,
                 downloaded_by, download_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file_name, file_hash, file_path, file_type, file_size,
                extracted_text, image_phash, video_fingerprint,
                downloaded_by, datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False          # duplicate hash
    finally:
        conn.close()


def find_by_hash(file_hash: str) -> Optional[Tuple]:
    """Return the first download row matching *file_hash*, or None."""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM downloads WHERE file_hash = ?", (file_hash,)
        ).fetchone()
    finally:
        conn.close()


def get_all_downloads() -> List[Tuple]:
    """Return all download rows ordered newest-first."""
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT file_name, file_type, downloaded_by, download_time, file_path
            FROM   downloads
            ORDER  BY download_time DESC
            """
        ).fetchall()
    finally:
        conn.close()


def search_files_by_keyword(keyword: str) -> List[Tuple]:
    """Full-text keyword search across file name and extracted text."""
    conn = get_connection()
    like = f"%{keyword}%"
    try:
        return conn.execute(
            """
            SELECT file_name, file_path, downloaded_by, download_time
            FROM   downloads
            WHERE  file_name      LIKE ?
               OR  extracted_text LIKE ?
            ORDER  BY download_time DESC
            """,
            (like, like),
        ).fetchall()
    finally:
        conn.close()


def get_all_docs_for_similarity() -> List[Tuple]:
    """Return (id, extracted_text) rows for TF-IDF similarity checks."""
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT id, extracted_text
            FROM   downloads
            WHERE  extracted_text IS NOT NULL
              AND  extracted_text != ''
            """
        ).fetchall()
    finally:
        conn.close()


# ── Alerts ────────────────────────────────────────────────────────────────────

def insert_alert(
    alert_for: str,
    duplicate_type: str,
    similarity: float,
    new_file: str,
    new_path: str,
    orig_file: str,
    orig_path: str,
    orig_user: str,
    orig_time: str,
) -> int:
    """Insert a new alert and return its id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO alerts
                (alert_for, duplicate_type, similarity,
                 new_file_name, new_file_path,
                 original_file, original_path, original_user, original_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert_for, duplicate_type, similarity,
                new_file, new_path, orig_file, orig_path, orig_user, orig_time,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_alerts_for_user(username: str) -> List[Tuple]:
    """Return pending alerts for *username*."""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM alerts WHERE alert_for = ? AND status = 'pending'",
            (username,),
        ).fetchall()
    finally:
        conn.close()


def update_alert_status(alert_id: int, status: str) -> None:
    """Set *status* ('shown' | 'resolved') on a specific alert."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE alerts SET status = ? WHERE id = ?", (status, alert_id)
        )
        conn.commit()
    finally:
        conn.close()


def get_all_alerts() -> List[Tuple]:
    """Return every alert row, newest first."""
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM alerts ORDER BY created_time DESC"
        ).fetchall()
    finally:
        conn.close()


# ── Stats (for dashboard) ─────────────────────────────────────────────────────

def get_stats() -> dict:
    """Return a summary dict used by the dashboard."""
    conn = get_connection()
    try:
        total_files   = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
        total_alerts  = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        pending       = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE status='pending'"
        ).fetchone()[0]
        return {
            "total_files":  total_files,
            "total_alerts": total_alerts,
            "pending":      pending,
        }
    finally:
        conn.close()
