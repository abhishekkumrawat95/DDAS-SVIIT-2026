"""
DDAS – Monitor Service
Uses Watchdog to observe monitored folders and trigger duplicate detection
whenever a new file is created or moved into a watched directory.
"""

import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from db import db_helper, init_db
from detection import hash_engine, text_similarity, image_video_detect

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent
    _WATCHDOG_AVAILABLE = True
except ImportError:
    _WATCHDOG_AVAILABLE = False

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("ddas.service")

os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)


class DDASEventHandler(FileSystemEventHandler):
    """Handles file-system events from Watchdog."""

    def on_created(self, event):
        if not event.is_directory:
            self._process(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._process(event.dest_path)

    def _process(self, file_path: str) -> None:
        """Compute file metadata and check for duplicates."""
        try:
            # Give the file a moment to finish writing
            time.sleep(0.5)
            if not os.path.isfile(file_path):
                return

            info = hash_engine.get_file_info(file_path)
            username = os.getenv("USERNAME") or os.getenv("USER") or "unknown"
            logger.info("New file detected: %s (hash=%s)", info["file_name"], info["file_hash"])

            # Check for exact duplicate by hash
            existing = db_helper.find_by_hash(info["file_hash"])
            if existing:
                orig_file = existing[1]   # file_name column
                orig_path = existing[3]   # file_path column
                orig_user = existing[9]   # downloaded_by column
                orig_time = existing[10]  # download_time column
                logger.warning("Exact duplicate detected: %s == %s", info["file_name"], orig_file)
                db_helper.insert_alert(
                    alert_for=username,
                    duplicate_type="exact",
                    similarity=100.0,
                    new_file=info["file_name"],
                    new_path=info["file_path"],
                    orig_file=orig_file,
                    orig_path=orig_path,
                    orig_user=orig_user,
                    orig_time=orig_time,
                )
                return  # Don't insert the duplicate into downloads

            # Extract additional metadata based on file type
            extracted_text = None
            image_phash = None
            video_fingerprint = None

            if info["file_type"] == "document":
                extracted_text = text_similarity.extract_text(file_path)
                if extracted_text:
                    corpus = db_helper.get_all_docs_for_similarity()
                    similar = text_similarity.find_similar_in_corpus(extracted_text, corpus)
                    if similar:
                        doc_id, score = similar[0]
                        logger.warning(
                            "Text-similar duplicate for %s (score=%.2f)", info["file_name"], score
                        )

            elif info["file_type"] == "image":
                image_phash = image_video_detect.compute_image_phash(file_path)

            elif info["file_type"] == "video":
                video_fingerprint = image_video_detect.compute_video_fingerprint(file_path)

            # Insert into database
            db_helper.insert_download(
                file_name=info["file_name"],
                file_hash=info["file_hash"],
                file_path=info["file_path"],
                file_type=info["file_type"],
                file_size=info["file_size"],
                downloaded_by=username,
                extracted_text=extracted_text,
                image_phash=image_phash,
                video_fingerprint=video_fingerprint,
            )
            logger.info("Stored: %s", info["file_name"])

        except Exception as exc:
            logger.error("Error processing %s: %s", file_path, exc, exc_info=True)


def run_service(folders=None):
    """Start the Watchdog observer for all monitored folders."""
    if not _WATCHDOG_AVAILABLE:
        logger.error("watchdog package not installed. Run: pip install watchdog")
        return

    # Ensure DB exists
    init_db.init_database()

    folders = folders or config.MONITOR_FOLDERS
    observer = Observer()
    handler = DDASEventHandler()

    started = 0
    for folder in folders:
        if os.path.isdir(folder):
            observer.schedule(handler, folder, recursive=False)
            logger.info("Monitoring folder: %s", folder)
            started += 1
        else:
            logger.warning("Folder not found, skipping: %s", folder)

    if started == 0:
        logger.error("No valid folders to monitor. Exiting.")
        return

    observer.start()
    logger.info("DDAS Monitor Service started. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(config.SCAN_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Stopping DDAS Monitor Service…")
    finally:
        observer.stop()
        observer.join()
        logger.info("DDAS Monitor Service stopped.")


if __name__ == "__main__":
    run_service()
