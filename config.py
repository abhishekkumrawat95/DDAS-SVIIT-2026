"""
DDAS – Data Download Duplication Alert System
Configuration management (cross-platform)
"""

import os
import sys
from pathlib import Path

# ── Base paths ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent

# Cross-platform data directory
if sys.platform == "win32":
    _DATA_ROOT = Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "DDAS"
elif sys.platform == "darwin":
    _DATA_ROOT = Path.home() / "Library" / "Application Support" / "DDAS"
else:
    _DATA_ROOT = Path.home() / ".ddas"

DATA_DIR = _DATA_ROOT
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH = str(DATA_DIR / "ddas.db")

# ── Monitoring ────────────────────────────────────────────────────────────────
WATCH_FOLDER = str(
    Path(os.environ.get("DDAS_WATCH_FOLDER",
                        str(Path.home() / "Downloads")))
)

# Username fallback (current OS user)
DEFAULT_USER = os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"

# ── Detection thresholds ──────────────────────────────────────────────────────
TEXT_SIMILARITY_THRESHOLD = float(os.environ.get("TEXT_SIM_THRESHOLD", "0.75"))
IMAGE_HASH_THRESHOLD = int(os.environ.get("IMAGE_HASH_THRESHOLD", "10"))  # hamming distance

# ── Notification ──────────────────────────────────────────────────────────────
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK", "")

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_FILE = str(DATA_DIR / "ddas.log")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# ── Auto-start ───────────────────────────────────────────────────────────────
# When True, launcher.py registers DDAS in the Windows startup registry so the
# monitor begins automatically after every reboot (Windows only).
AUTOSTART_ENABLED = os.environ.get("DDAS_AUTOSTART", "0") == "1"

# Registry key path used for auto-start (HKLM Run key – system-wide)
AUTOSTART_REG_KEY  = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_REG_NAME = "DDASMonitor"

# ── Dashboard ─────────────────────────────────────────────────────────────────
DASHBOARD_REFRESH_MS = int(os.environ.get("DASHBOARD_REFRESH_MS", "5000"))
