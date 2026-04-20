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


def search_files_by_type(file_type: str) -> List[Tuple]:
    """Return all downloads whose file_type matches *file_type* (case-insensitive)."""
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT file_name, file_type, downloaded_by, download_time, file_path
            FROM   downloads
            WHERE  file_type LIKE ?
            ORDER  BY download_time DESC
            """,
            (f"%{file_type}%",),
        ).fetchall()
    finally:
        conn.close()


def search_files_by_user(username: str) -> List[Tuple]:
    """Return all downloads attributed to *username* (partial match, case-insensitive)."""
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT file_name, file_type, downloaded_by, download_time, file_path
            FROM   downloads
            WHERE  downloaded_by LIKE ?
            ORDER  BY download_time DESC
            """,
            (f"%{username}%",),
        ).fetchall()
    finally:
        conn.close()


def search_files_by_date_range(start_date: str, end_date: str) -> List[Tuple]:
    """
    Return downloads whose download_time falls in [start_date, end_date).
    Dates should be ISO-format strings, e.g. '2026-04-01' or '2026-04-01T00:00:00'.
    """
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT file_name, file_type, downloaded_by, download_time, file_path
            FROM   downloads
            WHERE  download_time >= ? AND download_time < ?
            ORDER  BY download_time DESC
            """,
            (start_date, end_date),
        ).fetchall()
    finally:
        conn.close()


def search_files_by_size(min_bytes: int = 0, max_bytes: int = -1) -> List[Tuple]:
    """
    Return downloads filtered by file size.
    Pass *max_bytes* = -1 (default) to apply no upper bound.
    """
    conn = get_connection()
    try:
        if max_bytes < 0:
            return conn.execute(
                """
                SELECT file_name, file_type, file_size, downloaded_by, download_time, file_path
                FROM   downloads
                WHERE  file_size >= ?
                ORDER  BY file_size DESC
                """,
                (min_bytes,),
            ).fetchall()
        return conn.execute(
            """
            SELECT file_name, file_type, file_size, downloaded_by, download_time, file_path
            FROM   downloads
            WHERE  file_size >= ? AND file_size <= ?
            ORDER  BY file_size DESC
            """,
            (min_bytes, max_bytes),
        ).fetchall()
    finally:
        conn.close()


def get_cross_user_duplicates(user1: str = "", user2: str = "") -> List[Tuple]:
    """
    Return pairs of rows that share the same hash but were downloaded by different users.
    Optionally restrict to rows involving *user1* and/or *user2*.
    Each returned tuple is:
        (file_name_a, user_a, time_a, file_name_b, user_b, time_b)
    """
    conn = get_connection()
    try:
        if user1 and user2:
            return conn.execute(
                """
                SELECT a.file_name, a.downloaded_by, a.download_time,
                       b.file_name, b.downloaded_by, b.download_time
                FROM   downloads a
                JOIN   downloads b
                       ON  a.file_hash = b.file_hash
                       AND a.id < b.id
                       AND a.downloaded_by != b.downloaded_by
                WHERE  (a.downloaded_by LIKE ? AND b.downloaded_by LIKE ?)
                    OR (a.downloaded_by LIKE ? AND b.downloaded_by LIKE ?)
                ORDER  BY a.download_time DESC
                """,
                (f"%{user1}%", f"%{user2}%", f"%{user2}%", f"%{user1}%"),
            ).fetchall()
        if user1:
            return conn.execute(
                """
                SELECT a.file_name, a.downloaded_by, a.download_time,
                       b.file_name, b.downloaded_by, b.download_time
                FROM   downloads a
                JOIN   downloads b
                       ON  a.file_hash = b.file_hash
                       AND a.id < b.id
                       AND a.downloaded_by != b.downloaded_by
                WHERE  a.downloaded_by LIKE ? OR b.downloaded_by LIKE ?
                ORDER  BY a.download_time DESC
                """,
                (f"%{user1}%", f"%{user1}%"),
            ).fetchall()
        return conn.execute(
            """
            SELECT a.file_name, a.downloaded_by, a.download_time,
                   b.file_name, b.downloaded_by, b.download_time
            FROM   downloads a
            JOIN   downloads b
                   ON  a.file_hash = b.file_hash
                   AND a.id < b.id
                   AND a.downloaded_by != b.downloaded_by
            ORDER  BY a.download_time DESC
            """
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
