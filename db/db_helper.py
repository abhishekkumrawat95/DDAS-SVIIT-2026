
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

DB_PATH = r"C:\ProgramData\DDAS\ddas.db"

def get_connection():
    """Get SQLite connection with WAL mode"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def insert_download(file_name: str, file_hash: str, file_path: str, 
                   file_type: str, file_size: int, downloaded_by: str,
                   extracted_text: str = None, image_phash: str = None,
                   video_fingerprint: str = None) -> bool:
    """Insert new download record"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO downloads 
            (file_name, file_hash, file_path, file_type, file_size,
             extracted_text, image_phash, video_fingerprint,
             downloaded_by, download_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (file_name, file_hash, file_path, file_type, file_size,
              extracted_text, image_phash, video_fingerprint,
              downloaded_by, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  

def find_by_hash(file_hash: str) -> Optional[Tuple]:
    """Find exact duplicate by SHA256 hash"""
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT * FROM downloads WHERE file_hash = ?", (file_hash,)
    ).fetchone()
    conn.close()
    return row

def get_all_downloads() -> List[Tuple]:
    """Get all downloads for dashboard"""
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT file_name, file_type, downloaded_by, download_time, file_path 
        FROM downloads ORDER BY download_time DESC
    """).fetchall()
    conn.close()
    return rows

def insert_alert(alert_for: str, duplicate_type: str, similarity: float,
                new_file: str, new_path: str, orig_file: str,
                orig_path: str, orig_user: str, orig_time: str) -> int:
    """Insert new alert"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alerts (alert_for, duplicate_type, similarity,
                          new_file_name, new_file_path, original_file,
                          original_path, original_user, original_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (alert_for, duplicate_type, similarity, new_file, new_path,
          orig_file, orig_path, orig_user, orig_time))
    alert_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return alert_id

def get_alerts_for_user(username: str) -> List[Tuple]:
    """Get pending alerts for specific user"""
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT * FROM alerts 
        WHERE alert_for = ? AND status = 'pending'
    """, (username,)).fetchall()
    conn.close()
    return rows

def update_alert_status(alert_id: int, status: str):
    """Mark alert as shown/resolved"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE alerts SET status = ? WHERE id = ?",
        (status, alert_id)
    )
    conn.commit()
    conn.close()

def search_files_by_keyword(keyword: str) -> List[Tuple]:
    """Chatbot search functionality"""
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT file_name, file_path, downloaded_by, download_time
        FROM downloads
        WHERE file_name LIKE ? OR extracted_text LIKE ?
        ORDER BY download_time DESC
    """, (f"%{keyword}%", f"%{keyword}%")).fetchall()
    conn.close()
    return rows

def get_all_docs_for_similarity() -> List[Tuple]:
    """Get all document texts for TF-IDF"""
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT id, extracted_text FROM downloads 
        WHERE extracted_text IS NOT NULL AND extracted_text != ''
    """).fetchall()
    conn.close()
    return rows
