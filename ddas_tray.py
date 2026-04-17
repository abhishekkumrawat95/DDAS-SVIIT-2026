"""
DDAS – System Tray Application
Runs a persistent tray icon that shows notification alerts for new duplicates.
Requires: pystray, Pillow, plyer
"""

import os
import sys
import time
import threading
import getpass
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import db_helper
from db.init_db import init_database

log = logging.getLogger("ddas.tray")

# ---------------------------------------------------------------------------
# Optional imports
# ---------------------------------------------------------------------------
try:
    import pystray
    from pystray import MenuItem as item
    _PYSTRAY = True
except ImportError:
    _PYSTRAY = False
    log.warning("pystray not available – tray icon disabled.")

try:
    from PIL import Image, ImageDraw
    _PIL = True
except ImportError:
    _PIL = False

try:
    from plyer import notification as plyer_notify
    _PLYER = True
except ImportError:
    _PLYER = False


# ---------------------------------------------------------------------------
# Tray icon image (generated programmatically)
# ---------------------------------------------------------------------------

def _create_tray_icon() -> "Image.Image | None":
    """Create a simple 64×64 tray icon."""
    if not _PIL:
        return None
    img = Image.new("RGB", (64, 64), color=(30, 30, 46))
    draw = ImageDraw.Draw(img)
    # Shield shape
    draw.polygon(
        [(32, 4), (58, 16), (58, 40), (32, 60), (6, 40), (6, 16)],
        fill=(137, 180, 250),
    )
    draw.text((22, 24), "D", fill=(30, 30, 46))
    return img


# ---------------------------------------------------------------------------
# Desktop notification helper
# ---------------------------------------------------------------------------

def send_desktop_notification(title: str, message: str):
    """Send a desktop notification using plyer (cross-platform)."""
    if _PLYER:
        try:
            plyer_notify.notify(
                title=title,
                message=message,
                app_name="DDAS",
                timeout=8,
            )
            return
        except Exception:
            pass
    # Fallback: print to terminal
    print(f"\n🔔 [{title}] {message}")


# ---------------------------------------------------------------------------
# Alert poller
# ---------------------------------------------------------------------------

class AlertPoller(threading.Thread):
    """Background thread that polls for new pending alerts and notifies."""

    POLL_INTERVAL = 15  # seconds

    def __init__(self, username: str):
        super().__init__(daemon=True)
        self.username = username
        self._seen_ids: set = set()
        self._running = True

    def run(self):
        while self._running:
            try:
                self._check_alerts()
            except Exception as exc:
                log.debug("Alert poll error: %s", exc)
            time.sleep(self.POLL_INTERVAL)

    def _check_alerts(self):
        alerts = db_helper.get_alerts_for_user(self.username)
        for row in alerts:
            alert_id = row[0]
            if alert_id in self._seen_ids:
                continue
            self._seen_ids.add(alert_id)
            dup_type = row[2] if len(row) > 2 else "Duplicate"
            new_file = row[4] if len(row) > 4 else "unknown"
            orig_file = row[6] if len(row) > 6 else "unknown"
            send_desktop_notification(
                f"DDAS – {dup_type} Detected",
                f"'{new_file}' duplicates '{orig_file}'",
            )
            db_helper.update_alert_status(alert_id, "shown")

    def stop(self):
        self._running = False


# ---------------------------------------------------------------------------
# Tray application
# ---------------------------------------------------------------------------

def _open_dashboard(_icon=None, _item=None):
    """Launch the Tkinter dashboard in a subprocess to avoid threading issues."""
    import subprocess
    dashboard = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ddas_dashboard.py")
    subprocess.Popen([sys.executable, dashboard])


def _quit_app(icon, _item=None):
    icon.stop()


def run_tray(username: str = "unknown"):
    """Start the system tray icon and alert poller."""
    init_database()

    poller = AlertPoller(username)
    poller.start()

    if not _PYSTRAY or not _PIL:
        log.warning("System tray unavailable. Running alert poller only.")
        log.info("DDAS Alert Poller running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            poller.stop()
        return

    icon_image = _create_tray_icon()
    menu = pystray.Menu(
        item("Open Dashboard", _open_dashboard, default=True),
        pystray.Menu.SEPARATOR,
        item("Quit DDAS", _quit_app),
    )
    icon = pystray.Icon("DDAS", icon_image, "DDAS Monitor", menu)
    log.info("DDAS Tray running. Right-click the tray icon for options.")
    try:
        icon.run()
    finally:
        poller.stop()


if __name__ == "__main__":
    username = getpass.getuser()
    run_tray(username)
