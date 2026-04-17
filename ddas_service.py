"""
DDAS – File Monitoring Service
Uses Watchdog to watch one or more folders for new/modified files.
On detection, runs duplicate checks (hash → text → image/video) and
inserts alerts into the database via db_helper.
"""

import os
import sys
import time
import logging
import getpass
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("[ERROR] watchdog is not installed. Run: pip install watchdog")
    sys.exit(1)

from db import db_helper
from db.init_db import init_database
from detection.hash_engine import get_file_info, hash_file
from detection.text_similarity import (
    extract_text_from_file, find_similar_documents, is_text_file,
)
from detection.image_video_detect import (
    compute_image_phash, compute_video_fingerprint,
    is_image_file, is_video_file,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("ddas.service")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TEXT_SIM_THRESHOLD = 0.75   # 75% similarity → near-duplicate
IMG_SIM_THRESHOLD  = 10     # Hamming distance ≤ 10 → similar image

# File extensions the service cares about (add more as needed)
MONITORED_EXTENSIONS = {
    # Documents
    ".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".pptx", ".ppt",
    ".csv", ".md",
    # Images
    ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp",
    # Videos
    ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv",
    # Code / data
    ".py", ".js", ".json", ".xml", ".zip", ".tar", ".gz",
}


# ---------------------------------------------------------------------------
# Event handler
# ---------------------------------------------------------------------------

class DDASEventHandler(FileSystemEventHandler):
    """Handles file-system events from Watchdog."""

    def __init__(self, username: str = "unknown"):
        super().__init__()
        self.username = username
        self._processing: set = set()  # guard against double-processing

    def on_created(self, event):
        if event.is_directory:
            return
        self._handle_file(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        self._handle_file(event.dest_path)

    def _handle_file(self, filepath: str):
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in MONITORED_EXTENSIONS:
            return
        if filepath in self._processing:
            return
        self._processing.add(filepath)
        try:
            # Brief pause so OS can finish writing the file
            time.sleep(0.5)
            process_new_file(filepath, self.username)
        finally:
            self._processing.discard(filepath)


# ---------------------------------------------------------------------------
# Core duplicate-checking logic
# ---------------------------------------------------------------------------

def process_new_file(filepath: str, username: str = "unknown"):
    """
    Run all duplicate checks on *filepath* and persist results to the DB.
    """
    if not os.path.isfile(filepath):
        return

    log.info("Checking: %s", filepath)
    info = get_file_info(filepath)
    if not info or not info.get("file_hash"):
        log.warning("Could not hash file: %s", filepath)
        return

    # ------------------------------------------------------------------
    # 1. Exact hash match
    # ------------------------------------------------------------------
    existing = db_helper.find_by_hash(info["file_hash"])
    if existing:
        orig_name = existing[1]   # file_name column
        orig_path = existing[3]   # file_path column
        orig_user = existing[9] if len(existing) > 9 else "unknown"
        orig_time = existing[10] if len(existing) > 10 else ""
        log.warning("EXACT DUPLICATE: %s == %s", info["file_name"], orig_name)
        db_helper.insert_alert(
            alert_for=username,
            duplicate_type="ExactHash",
            similarity=100.0,
            new_file=info["file_name"],
            new_path=filepath,
            orig_file=orig_name,
            orig_path=orig_path,
            orig_user=orig_user,
            orig_time=orig_time,
        )
        return  # no need to add to downloads table

    # ------------------------------------------------------------------
    # 2. Text similarity check
    # ------------------------------------------------------------------
    extracted_text = None
    if is_text_file(filepath):
        extracted_text = extract_text_from_file(filepath)
        if extracted_text:
            all_docs = db_helper.get_all_docs_for_similarity()
            similar = find_similar_documents(extracted_text, all_docs, TEXT_SIM_THRESHOLD)
            for doc_id, score in similar:
                orig_row = _get_download_by_id(doc_id)
                if orig_row:
                    log.warning(
                        "TEXT SIMILAR (%.0f%%): %s ≈ %s",
                        score * 100, info["file_name"], orig_row[1],
                    )
                    db_helper.insert_alert(
                        alert_for=username,
                        duplicate_type="TextSimilar",
                        similarity=round(score * 100, 2),
                        new_file=info["file_name"],
                        new_path=filepath,
                        orig_file=orig_row[1],
                        orig_path=orig_row[3],
                        orig_user=orig_row[9] if len(orig_row) > 9 else "unknown",
                        orig_time=orig_row[10] if len(orig_row) > 10 else "",
                    )

    # ------------------------------------------------------------------
    # 3. Image perceptual hash check
    # ------------------------------------------------------------------
    image_phash = None
    if is_image_file(filepath):
        image_phash = compute_image_phash(filepath)
        if image_phash:
            similar_img = _find_similar_images(image_phash)
            for orig_row in similar_img:
                log.warning(
                    "IMAGE SIMILAR: %s ≈ %s", info["file_name"], orig_row[1]
                )
                db_helper.insert_alert(
                    alert_for=username,
                    duplicate_type="ImageSimilar",
                    similarity=90.0,
                    new_file=info["file_name"],
                    new_path=filepath,
                    orig_file=orig_row[1],
                    orig_path=orig_row[3],
                    orig_user=orig_row[9] if len(orig_row) > 9 else "unknown",
                    orig_time=orig_row[10] if len(orig_row) > 10 else "",
                )

    # ------------------------------------------------------------------
    # 4. Video fingerprint check
    # ------------------------------------------------------------------
    video_fp = None
    if is_video_file(filepath):
        video_fp = compute_video_fingerprint(filepath)
        if video_fp:
            similar_vid = _find_similar_videos(video_fp)
            for orig_row in similar_vid:
                log.warning(
                    "VIDEO SIMILAR: %s ≈ %s", info["file_name"], orig_row[1]
                )
                db_helper.insert_alert(
                    alert_for=username,
                    duplicate_type="VideoSimilar",
                    similarity=85.0,
                    new_file=info["file_name"],
                    new_path=filepath,
                    orig_file=orig_row[1],
                    orig_path=orig_row[3],
                    orig_user=orig_row[9] if len(orig_row) > 9 else "unknown",
                    orig_time=orig_row[10] if len(orig_row) > 10 else "",
                )

    # ------------------------------------------------------------------
    # 5. Register new file in downloads table
    # ------------------------------------------------------------------
    db_helper.insert_download(
        file_name=info["file_name"],
        file_hash=info["file_hash"],
        file_path=filepath,
        file_type=info["file_type"],
        file_size=info["file_size"],
        downloaded_by=username,
        extracted_text=extracted_text,
        image_phash=image_phash,
        video_fingerprint=video_fp,
    )
    log.info("Registered: %s", info["file_name"])


# ---------------------------------------------------------------------------
# Private DB helpers
# ---------------------------------------------------------------------------

def _get_download_by_id(doc_id: int):
    conn = db_helper.get_connection()
    row = conn.execute("SELECT * FROM downloads WHERE id = ?", (doc_id,)).fetchone()
    conn.close()
    return row


def _find_similar_images(phash: str):
    """Return download rows whose image_phash is within the threshold."""
    from detection.image_video_detect import image_hash_distance
    conn = db_helper.get_connection()
    rows = conn.execute(
        "SELECT * FROM downloads WHERE image_phash IS NOT NULL AND image_phash != ''"
    ).fetchall()
    conn.close()
    return [
        r for r in rows
        if image_hash_distance(phash, r[7]) <= IMG_SIM_THRESHOLD  # image_phash col
    ]


def _find_similar_videos(fingerprint: str):
    """Return download rows whose video fingerprint is similar."""
    from detection.image_video_detect import videos_are_similar
    conn = db_helper.get_connection()
    rows = conn.execute(
        "SELECT * FROM downloads WHERE video_fingerprint IS NOT NULL AND video_fingerprint != ''"
    ).fetchall()
    conn.close()
    return [r for r in rows if videos_are_similar(fingerprint, r[8])]


# ---------------------------------------------------------------------------
# Service entry-point
# ---------------------------------------------------------------------------

def start_monitoring(folders: list, username: str = "unknown"):
    """
    Start Watchdog observers for each folder in *folders*.
    Blocks until the user interrupts with Ctrl-C.
    """
    if not folders:
        log.error("No folders to monitor. Exiting.")
        return

    handler = DDASEventHandler(username=username)
    observer = Observer()
    for folder in folders:
        if os.path.isdir(folder):
            observer.schedule(handler, folder, recursive=True)
            log.info("Monitoring: %s", folder)
        else:
            log.warning("Skipping (not a directory): %s", folder)

    observer.start()
    log.info("DDAS Monitor running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Stopping monitor…")
        observer.stop()
    observer.join()


# ---------------------------------------------------------------------------
# __main__ – quick interactive start
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_database()
    username = getpass.getuser()

    if len(sys.argv) > 1:
        watch_folders = sys.argv[1:]
    else:
        default_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        watch_folders = [default_folder]
        log.info("No folder specified – watching: %s", default_folder)

    start_monitoring(watch_folders, username)
