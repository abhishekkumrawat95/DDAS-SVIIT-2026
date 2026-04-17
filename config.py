"""
DDAS – Data Download Duplication Alert System
Configuration management – reads from environment variables with sensible defaults.
"""

import os
from pathlib import Path

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
SCAN_INTERVAL = int(os.getenv("DDAS_SCAN_INTERVAL", "5"))

# ── Duplicate-Detection Thresholds ────────────────────────────────────────────
TEXT_SIMILARITY_THRESHOLD = float(os.getenv("TEXT_SIMILARITY_THRESHOLD", "0.85"))
IMAGE_HASH_THRESHOLD = int(os.getenv("IMAGE_HASH_THRESHOLD", "10"))

# ── Email Notifications ───────────────────────────────────────────────────────
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

# ── REST API ──────────────────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "5000"))
API_DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"

# ── Chatbot ───────────────────────────────────────────────────────────────────
ONLINE_SEARCH_ENABLED = os.getenv("ONLINE_SEARCH_ENABLED", "false").lower() == "true"
ONLINE_SEARCH_MAX_RESULTS = int(os.getenv("ONLINE_SEARCH_MAX_RESULTS", "5"))

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "data" / "ddas.log"))
