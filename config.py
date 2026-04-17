"""
DDAS – Data Download Duplication Alert System
Configuration management – reads from environment variables with sensible defaults.
"""

import os
import sys
from pathlib import Path


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name, str(default))
    try:
        return int(value)
    except ValueError:
        print(f"[DDAS config] Warning: {name}={value!r} is not a valid integer, using default {default}.", file=sys.stderr)
        return default


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name, str(default))
    try:
        return float(value)
    except ValueError:
        print(f"[DDAS config] Warning: {name}={value!r} is not a valid float, using default {default}.", file=sys.stderr)
        return default


# ── Project root ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH = os.getenv("DDAS_DB_PATH", str(BASE_DIR / "data" / "ddas.db"))

# ── File Monitoring ───────────────────────────────────────────────────────────
_default_folders = str(Path.home() / "Downloads")
MONITOR_FOLDERS = [
    f.strip()
    for f in os.getenv("DDAS_MONITOR_FOLDERS", _default_folders).split(",")
    if f.strip()
]
SCAN_INTERVAL = _get_int("DDAS_SCAN_INTERVAL", 5)

# ── Duplicate-Detection Thresholds ────────────────────────────────────────────
TEXT_SIMILARITY_THRESHOLD = _get_float("TEXT_SIMILARITY_THRESHOLD", 0.85)
IMAGE_HASH_THRESHOLD = _get_int("IMAGE_HASH_THRESHOLD", 10)

# ── Email Notifications ───────────────────────────────────────────────────────
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = _get_int("EMAIL_PORT", 587)
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

# ── REST API ──────────────────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = _get_int("API_PORT", 5000)
API_DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"

# ── Chatbot ───────────────────────────────────────────────────────────────────
ONLINE_SEARCH_ENABLED = os.getenv("ONLINE_SEARCH_ENABLED", "false").lower() == "true"
ONLINE_SEARCH_MAX_RESULTS = _get_int("ONLINE_SEARCH_MAX_RESULTS", 5)

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "data" / "ddas.log"))
