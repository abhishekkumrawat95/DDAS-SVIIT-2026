"""
DDAS – File Monitoring Service
Uses watchdog to watch a folder and detect duplicate downloads in real time.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from config import WATCH_FOLDER, DEFAULT_USER, TEXT_SIMILARITY_THRESHOLD, IMAGE_HASH_THRESHOLD, LOG_FILE, LOG_LEVEL
from db.init_db import init_db
from db.db_helper import (
    insert_download, find_by_hash,
    get_all_docs_for_similarity, insert_alert,
)
from detection.hash_engine import sha256, file_type, file_size
from detection.text_similarity import extract_text_from_file, find_similar
from detection.image_video_detect import (
    image_phash, video_fingerprint,
    is_image, is_video, images_are_similar, videos_are_similar,
)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent
    _HAS_WATCHDOG = True
except ImportError:
    _HAS_WATCHDOG = False


# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("ddas.service")

# Delay after a file-created event before hashing, allowing the OS to finish
# writing the file (e.g. browser completing a download).
FILE_WRITE_DELAY_SECONDS = 1


# ── Duplicate check ───────────────────────────────────────────────────────────

def _notify(msg: str) -> None:
    """Desktop notification (best-effort via plyer)."""
    try:
        from plyer import notification
        notification.notify(title="DDAS Alert", message=msg, timeout=8)
    except Exception:
        pass  # plyer not available or headless environment


def process_file(path: str, user: str = DEFAULT_USER) -> None:
    """
    Hash the file, check for duplicates, insert into DB or raise an alert.
    Called both by the watchdog handler and by manual scans.
    """
    p = Path(path)
    if not p.is_file():
        return

    name  = p.name
    ftype = file_type(p)
    fsize = file_size(p)

    log.info("Processing: %s (%s, %d bytes)", name, ftype, fsize)

    # ── 1. Exact duplicate (SHA-256 hash) ────────────────────────────────────
    digest = sha256(p)
    if digest is None:
        log.warning("Could not hash %s – skipping.", name)
        return

    existing = find_by_hash(digest)
    if existing:
        log.warning("EXACT DUPLICATE detected: %s == %s", name, existing[1])
        _notify(f"Duplicate! '{name}' is identical to '{existing[1]}'")
        insert_alert(
            alert_for=user,
            duplicate_type="exact",
            similarity=1.0,
            new_file=name,
            new_path=str(p),
            orig_file=existing[1],
            orig_path=existing[3],
            orig_user=existing[9] or "",
            orig_time=existing[10] or "",
        )
        return   # don't store the duplicate itself

    # ── 2. Image similarity (pHash) ──────────────────────────────────────────
    phash_val = None
    if is_image(p):
        phash_val = image_phash(p)

    # ── 3. Video similarity ──────────────────────────────────────────────────
    vfp = None
    if is_video(p):
        vfp = video_fingerprint(p)

    # ── 4. Text similarity (TF-IDF) ──────────────────────────────────────────
    ext_text = None
    text_result = None
    if ftype in {"txt", "pdf", "docx", "csv", "md", "html", "py", "js"}:
        ext_text = extract_text_from_file(p)
        if ext_text:
            corpus = get_all_docs_for_similarity()
            text_result = find_similar(ext_text, corpus, threshold=TEXT_SIMILARITY_THRESHOLD)
            if text_result:
                orig_id, score = text_result
                log.warning(
                    "TEXT SIMILAR: %s ~ DB#%d (score %.2f)", name, orig_id, score
                )
                _notify(f"Similar document! '{name}' resembles a previously stored file.")
                insert_alert(
                    alert_for=user,
                    duplicate_type="text_similar",
                    similarity=score,
                    new_file=name,
                    new_path=str(p),
                    orig_file=f"db_id:{orig_id}",
                    orig_path="",
                    orig_user="",
                    orig_time="",
                )

    # ── 5. Store new file record ──────────────────────────────────────────────
    ok = insert_download(
        file_name=name,
        file_hash=digest,
        file_path=str(p),
        file_type=ftype,
        file_size=fsize,
        downloaded_by=user,
        extracted_text=ext_text,
        image_phash=phash_val,
        video_fingerprint=vfp,
    )
    if ok:
        log.info("Stored: %s", name)
    else:
        log.debug("Already in DB (race condition avoided): %s", name)


# ── Watchdog handler ──────────────────────────────────────────────────────────

class _DownloadHandler(FileSystemEventHandler if _HAS_WATCHDOG else object):
    """React to newly created files in the watched folder."""

    def on_created(self, event: "FileCreatedEvent") -> None:  # type: ignore[override]
        if event.is_directory:
            return
        # Wait for the OS to finish writing the file before hashing
        time.sleep(FILE_WRITE_DELAY_SECONDS)
        try:
            process_file(event.src_path)
        except Exception as exc:
            log.error("Error processing %s: %s", event.src_path, exc)


# ── Entry point ───────────────────────────────────────────────────────────────

_observer: "Observer | None" = None
_observer_lock = threading.Lock()


def stop() -> None:
    """Signal the monitoring loop to stop (safe to call from any thread)."""
    with _observer_lock:
        if _observer is not None:
            _observer.stop()
            log.info("DDAS monitor stop requested.")


def start(watch_folder: str = WATCH_FOLDER) -> None:
    """Start the monitoring loop (blocks until KeyboardInterrupt or stop())."""
    global _observer

    if not _HAS_WATCHDOG:
        log.error("watchdog library not installed. Run: pip install watchdog")
        sys.exit(1)

    init_db()

    folder = Path(watch_folder)
    folder.mkdir(parents=True, exist_ok=True)

    obs = Observer()
    obs.schedule(_DownloadHandler(), str(folder), recursive=False)
    obs.start()
    with _observer_lock:
        _observer = obs
    log.info("DDAS monitoring started. Watching: %s", folder)
    print(f"[DDAS] Monitoring '{folder}' — press Ctrl+C to stop.")

    try:
        while obs.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Shutdown requested.")
    finally:
        obs.stop()
        obs.join()
        with _observer_lock:
            _observer = None
        log.info("DDAS monitor stopped.")


if __name__ == "__main__":
    folder_arg = sys.argv[1] if len(sys.argv) > 1 else WATCH_FOLDER
    start(folder_arg)
