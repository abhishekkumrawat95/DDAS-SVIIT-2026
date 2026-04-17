"""
DDAS – System Tray Icon
Provides a tray icon with start/stop monitor and open-dashboard actions.
"""

from __future__ import annotations

import os
import sys
import threading

sys.path.insert(0, os.path.dirname(__file__))

try:
    import pystray
    from PIL import Image, ImageDraw
    _HAS_TRAY = True
except ImportError:
    _HAS_TRAY = False

import ddas_service
from db.init_db import init_db


# ── Icon builder ──────────────────────────────────────────────────────────────

def _make_icon(color: str = "#4a90d9") -> "Image.Image":
    """Create a simple coloured circle as the tray icon."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill=color)
    draw.text((18, 20), "D", fill="white")
    return img


# ── Monitor thread ────────────────────────────────────────────────────────────

_monitor_thread: threading.Thread | None = None
_stop_event = threading.Event()


def _start_monitor() -> None:
    global _monitor_thread
    if _monitor_thread and _monitor_thread.is_alive():
        return
    _stop_event.clear()
    _monitor_thread = threading.Thread(target=ddas_service.start, daemon=True)
    _monitor_thread.start()


def _stop_monitor() -> None:
    _stop_event.set()


# ── Tray callbacks ────────────────────────────────────────────────────────────

def _on_start(icon, item) -> None:
    _start_monitor()
    icon.notify("DDAS Monitor started.", "DDAS")


def _on_stop(icon, item) -> None:
    _stop_monitor()
    icon.notify("DDAS Monitor stopped.", "DDAS")


def _on_dashboard(icon, item) -> None:
    import subprocess
    subprocess.Popen([sys.executable, "ddas_dashboard.py"])


def _on_quit(icon, item) -> None:
    _stop_monitor()
    icon.stop()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    if not _HAS_TRAY:
        print("pystray / Pillow not installed. Tray icon unavailable.")
        print("Starting monitor directly…")
        init_db()
        ddas_service.start()
        return

    init_db()
    _start_monitor()   # auto-start on launch

    menu = pystray.Menu(
        pystray.MenuItem("Start Monitor",  _on_start),
        pystray.MenuItem("Stop Monitor",   _on_stop),
        pystray.MenuItem("Open Dashboard", _on_dashboard),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit",           _on_quit),
    )
    icon = pystray.Icon("DDAS", _make_icon(), "DDAS Monitor", menu)
    icon.run()


if __name__ == "__main__":
    main()
