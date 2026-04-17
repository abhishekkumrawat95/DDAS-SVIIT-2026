"""
DDAS – System Tray Application
Shows a system-tray icon (Windows/Linux/macOS) and desktop notifications
when duplicate files are detected.
"""

import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from db import db_helper

try:
    import pystray
    from pystray import MenuItem as Item
    _PYSTRAY_AVAILABLE = True
except ImportError:
    _PYSTRAY_AVAILABLE = False

try:
    from plyer import notification as plyer_notification
    _PLYER_AVAILABLE = True
except ImportError:
    _PLYER_AVAILABLE = False

try:
    from PIL import Image, ImageDraw
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

import os

USERNAME = os.getenv("USERNAME") or os.getenv("USER") or "unknown"


def _create_icon_image(size=64, color=(0, 120, 215)):
    """Create a simple coloured circle as the tray icon."""
    if not _PIL_AVAILABLE:
        return None
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill=color)
    return img


def _notify(title: str, message: str) -> None:
    """Send a desktop notification."""
    if _PLYER_AVAILABLE:
        try:
            plyer_notification.notify(
                title=title,
                message=message,
                app_name="DDAS",
                timeout=5,
            )
        except Exception:
            pass
    else:
        print(f"[NOTIFICATION] {title}: {message}")


def _poll_alerts(stop_event: threading.Event) -> None:
    """Background thread: polls DB for pending alerts and shows notifications."""
    while not stop_event.is_set():
        try:
            alerts = db_helper.get_alerts_for_user(USERNAME)
            for alert in alerts:
                alert_id = alert[0]
                new_file = alert[4]
                orig_file = alert[6]
                _notify(
                    "DDAS – Duplicate Detected",
                    f"'{new_file}' is a duplicate of '{orig_file}'",
                )
                db_helper.update_alert_status(alert_id, "shown")
        except Exception:
            pass
        stop_event.wait(config.SCAN_INTERVAL)


def run_tray():
    """Launch the system-tray app with background alert polling."""
    stop_event = threading.Event()
    poll_thread = threading.Thread(target=_poll_alerts, args=(stop_event,), daemon=True)
    poll_thread.start()

    if not _PYSTRAY_AVAILABLE:
        print("[DDAS Tray] pystray not available – running in console mode.")
        print("  Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_event.set()
        return

    icon_image = _create_icon_image()

    def on_quit(icon, _item):
        stop_event.set()
        icon.stop()

    menu = pystray.Menu(
        Item("DDAS – Running", lambda *_: None, enabled=False),
        Item("Quit", on_quit),
    )

    icon = pystray.Icon(
        "DDAS",
        icon_image or Image.new("RGB", (64, 64), (0, 120, 215)),
        "DDAS Monitor",
        menu,
    )
    icon.run()


if __name__ == "__main__":
    run_tray()
